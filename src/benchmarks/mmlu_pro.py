import argparse
import json
import random
import sys
from collections import OrderedDict
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from datasets import load_dataset
from tqdm import tqdm


@dataclass
class Question:
    question_id: str
    category: str
    question: str
    options: List[str]
    answer: str
    answer_index: int
    cot_content: str
    src: str
    pred: Optional[Tuple] = None
    init_pred: Optional[Tuple] = None
    model_outputs: Optional[Tuple] = None
    init_outputs: Optional[Tuple] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


class MMPROEvaluator:
    def __init__(self, model1_name: str, model2_name: str, output_dir: str):
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = None
        self.test_df = None
        self.example_df = None
        
    def initialize_client(self):
        """Lazy initialization of the API client"""
        if self.client is None:
            from api.debate_api_model import DebateAPIModel
            self.client = DebateAPIModel(
                model1_name=self.model1_name,
                model2_name=self.model2_name
            )
        return self.client

    def load_mmlu_pro(self):
        if self.test_df is None or self.example_df is None:
            """Load and preprocess the MMLU-Pro dataset"""
            dataset = load_dataset("TIGER-Lab/MMLU-Pro")
            
            def preprocess_split(split_data):
                # Group questions by category
                processed = {}
                for item in split_data:
                    # Filter out N/A options
                    options = [opt for opt in item["options"] if opt != "N/A"]
                    item["options"] = options
                    
                    category = item["category"]
                    if category not in processed:
                        processed[category] = []
                    processed[category].append(item)
                return processed

            self.test_df = preprocess_split(dataset["test"])
            self.example_df = preprocess_split(dataset["validation"])


    def get_subjects(self):
        self.load_mmlu_pro()
        return list(self.test_df.keys())


    @staticmethod
    def format_example(question: str, options: List[str], 
                      question_number: int, cot_content: str = "") -> str:
        """Format a question example with options"""
        if not cot_content:
            cot_content = "Let's think step by step."
        elif cot_content.startswith("A: "):
            cot_content = cot_content[3:]
            
        example = [
            f"Question {question_number}: {question}",
            "\nOptions: "
        ]
        
        for i, opt in enumerate(options):
            example.append(f"{chr(65 + i)}. {opt}")
            
        example.extend([
            f"\nAnswer {question_number}: {cot_content}",
            "\n"
        ])
        
        return "\n".join(example)

    def build_prompt(self, category: str, example_questions: List[dict]) -> str:
        """Build the prompt for the model"""
        prompt_parts = [
            f"The following are example multiple choice questions (with answers) about {category}:\n\n"
        ]
        
        for i, q in enumerate(example_questions, 1):
            prompt_parts.append(
                self.format_example(
                    q["question"],
                    q["options"],
                    i,
                    q["cot_content"]
                )
            )
            
        prompt_parts.extend([
            "\n\nThe user is expected to ask a similar kind of question along with options for the correct answer.\n",
            "\nYou are supposed to deliberate, think step by step and then answer the user's question by choosing from the provided options.\n",
            "\nBefore choosing the answer, please present your indepth analysis.\n",
            "\nIf you are able to choose the correct answer from the provided options, please output the answer as `The answer is (X)` in the end.\n",
            "\nHowever, if you are unable to choose the correct answer, please output `I cannot determine the answer`.\n"
        ])
        
        return "".join(prompt_parts)

    def process_single_question(self, question: Question, cot_examples: List[dict], 
                              existing_results: Dict, retake: bool = False) -> Tuple:
        """Process a single question and return results"""
        if not retake and question.question_id in existing_results:
            result = existing_results[question.question_id]
            if question.question == result["question"]:
                from extract_answer import extract_answer
                return self._reevaluate_answers(result, extract_answer)

        prompt = self.build_prompt(question.category, cot_examples)
        input_text = self.format_example(
            question.question,
            question.options,
            len(cot_examples) + 1
        )

        try:
            log_dir = self.output_dir / "answers" / question.category.replace(" ", "_")
            log_filename = f"Question#{question.question_id}.md"
            
            print(f"Processing Question#{question.question_id}")
            
            client = self.initialize_client()
            responses = client.get_response(
                input_text,
                user_instructions=prompt,
                log_dir=log_dir,
                log_filename=log_filename
            )
            
            from benchmarks.extract_answer import extract_answer
            predictions = tuple(map(extract_answer, responses))
            
            print(f"Question#{question.question_id} answered. "
                  f"Consensus: {predictions[0] == predictions[1]}")
            
            return (
                predictions[:2],
                responses[:2],
                predictions[2:],
                responses[2:],
                False
            )
            
        except Exception as e:
            print(f"Error processing question {question.question_id}: {e}")
            return None, None, None, None, False

    @staticmethod
    def _reevaluate_answers(question_result: Dict, extract_fn) -> Tuple:
        """Re-evaluate answers from existing results"""
        responses = (
            question_result["model_outputs"],
            question_result["init_outputs"]
        )
        
        predictions = tuple(map(extract_fn, responses[0]))
        init_predictions = tuple(map(extract_fn, responses[1]))
        
        return (
            predictions,
            responses[0],
            init_predictions,
            responses[1],
            True
        )

    def evaluate_batch(self, subjects: Optional[List[str]] = None, batch_size: int = sys.maxsize, retake: bool = True):
        """Evaluate a batch of questions for a subject"""
        question_data, subjects, example_data = self.get_question_data(subjects, batch_size=batch_size)
        
        for subject in subjects:
            test_questions = question_data[subject]
            example_questions = example_data[subject]
            
            if len(test_questions) > batch_size:
                test_questions = random.sample(test_questions, batch_size)    
            results = self.load_results(subject)
            
            for item in tqdm(test_questions, desc=f"Evaluating {subject}"):
                question = Question(**item)
                pred, response, init_pred, init_response, _ = self.process_single_question(
                    question,
                    example_questions,
                    results,
                    retake=retake
                )
                
                if response is not None:
                    question.pred = pred
                    question.init_pred = init_pred
                    question.model_outputs = response
                    question.init_outputs = init_response
                    results[question.question_id] = question.to_dict()
                    self.save_results(subject, results, "question_id")
                    
            self.update_summary(subject, results)
            
    def get_question_data(self, subjects: Optional[List[str]] = None, question_number: int = -1, batch_size: int = sys.maxsize):
        """Evaluate a single question by its ID"""
        self.load_mmlu_pro()
        subjects = subjects or self.get_subjects()
        
        if question_number == -1:
            question_data = {}
            example_data = {}
            for subject in subjects:
                test_questions = self.test_df[subject]
                example_questions = self.example_df[subject]
                if len(test_questions) > batch_size:
                    test_questions = random.sample(test_questions, batch_size)                
                question_data[subject] = test_questions
                example_data[subject] = example_questions
            return question_data, subjects, example_data
        else:
            for subject in subjects:
                test_questions = self.test_df[subject]
                example_questions = self.example_df[subject]
                for test_question in test_questions:
                    if test_question["question_id"] == question_number:
                        return test_question, subject, example_questions
            return None, None, None


    def evaluate_single_question(self, question_number: int, subjects: Optional[List[str]] = None, retake: bool = True):
        """Evaluate a single question by its ID"""
        test_question, subject, example_questions = self.get_question_data(subjects, question_number)
        
        question = Question(**test_question)
        results = self.load_results(subject=subject)
        
        pred, response, init_pred, init_response, _ = self.process_single_question(
            question,
            example_questions,
            results,
            retake=retake
        )
        
        if response is not None:
            question.pred = pred
            question.init_pred = init_pred
            question.model_outputs = response
            question.init_outputs = init_response
            results[question.question_id] = question.to_dict()
            self.save_results(subject, results, "question_id")
            self.update_summary(subject, results)
            return
                    
        print(f"Question#{question_number} not found")

    def load_results(self, subject: str) -> Dict:
        """Load existing results from file"""
        filepath = self.output_dir / f"{subject.replace(' ', '_')}_result.json"
        if not filepath.exists():
            filepath.write_text("{}")
            return {}
        return {item['question_id']: item 
                for item in json.loads(filepath.read_text())}

    def save_results(self, subject: str, results: Dict, sort_key: Optional[str] = None):
        """Save results to file with optional sorting"""
        filepath = self.output_dir / f"{subject.replace(' ', '_')}_result.json"
        output_data = list(results.values())
        if sort_key:
            output_data.sort(key=lambda x: x.get(sort_key))
        filepath.write_text(json.dumps(output_data, indent=2))

    def update_summary(self, subject: str, results: Dict):
        """Update and save summary statistics"""
        summary_path = self.output_dir / "results_summary.json"
        
        if not summary_path.exists():
            summary_path.write_text("{}")
            
        summary = json.loads(summary_path.read_text())
        
        from statistics import update_summary
        update_summary(summary, subject, results)
        
        # Sort summary with 'overall' first
        sorted_summary = OrderedDict()
        if 'overall' in summary:
            sorted_summary['overall'] = summary['overall']
        for key in sorted(k for k in summary if k != 'overall'):
            sorted_summary[key] = summary[key]
            
        summary_path.write_text(json.dumps(sorted_summary, indent=2))


def main(args=None):
    parser = argparse.ArgumentParser(description='MMLU-Pro Evaluation Script')
    parser.add_argument("--output_dir", "-o", type=str, default="eval_results/")
    parser.add_argument("--model1_name", "-m1", type=str, required=True)
    parser.add_argument("--model2_name", "-m2", type=str, required=True)
    parser.add_argument("--subjects", "-s", type=str, default="all")
    parser.add_argument("--batch_size", "-b", type=int, default=sys.maxsize)
    parser.add_argument("--question", "-q", type=int, default=-1)
    parser.add_argument("--retake", "-r", type=bool, default=True)
    
    if args is None:
        args = sys.argv[1:]
    args = parser.parse_args(args=args)
    
    evaluator = MMPROEvaluator(
        model1_name=args.model1_name,
        model2_name=args.model2_name,
        output_dir=args.output_dir
    )
    
    subjects = None if args.subjects == "all" else args.subjects.split(",")
    
    if args.question != -1:
        evaluator.evaluate_single_question(args.question, subjects, args.retake)
    else:
        evaluator.evaluate_batch(subjects, args.batch_size, args.retake)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)