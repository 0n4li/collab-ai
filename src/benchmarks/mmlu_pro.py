import argparse
import os
import json
import random
import time
import sys
from collections import OrderedDict
from datasets import load_dataset
from tqdm import tqdm
from pathlib import Path

from api.debate_api_model import DebateAPIModel
from benchmarks.extract_answer import extract_answer
from benchmarks.statistics import update_summary

parsed_args = None

def preprocess(test_df):
    res_df = []
    for each in test_df:
        options = []
        for opt in each["options"]:
            if opt == "N/A":
                continue
            options.append(opt)
        each["options"] = options
        res_df.append(each)
    res = {}
    for each in res_df:
        if each["category"] not in res:
            res[each["category"]] = []
        res[each["category"]].append(each)
    return res


def load_mmlu_pro():
    dataset = load_dataset("TIGER-Lab/MMLU-Pro")
    test_df, val_df = dataset["test"], dataset["validation"]
    test_df = preprocess(test_df)
    val_df = preprocess(val_df)
    return test_df, val_df
    
    
def format_example(question, options, question_number, cot_content=""):
    if cot_content == "":
        cot_content = "Let's think step by step."
    if cot_content.startswith("A: "):
        cot_content = cot_content[3:]
    example = "Question {}: {}\n\nOptions: ".format(question_number, question)
    choice_map = "ABCDEFGHIJ"
    for i, opt in enumerate(options):
        example += "{}. {}\n".format(choice_map[i], opt)
    example += "\nAnswer: " + cot_content + "\n\n"
    return example


def build_prompt(category, example_questions):
    prompt = f"The following are example multiple choice questions (with answers) about {category}:\n\n"
    question_number = 1
    for each in example_questions:
        prompt += format_example(each["question"], each["options"], question_number, each["cot_content"])
        question_number += 1
    prompt += "\n\n"
    prompt += "The user is expected to ask a similar kind of question along with options for the correct answer.\n\n"
    prompt += "You are supposed to deliberate, think step by step and then answer the user's question by choosing from the provided options.\n\n"
    prompt += "Before choosing the answer, please present your indepth analysis.\n\n"
    prompt += "If you are able to choose the correct answer from the provided options, please output the answer as `The answer is (X)` in the end.\n\n"
    prompt += "However, if you are unable to choose the correct answer, please output `I cannot determine the answer`.\n\n"
    return prompt


def get_answers(final_response1, final_response2, initial_response1, initial_response2):
    pred1 = extract_answer(final_response1)
    pred2 = extract_answer(final_response2)
    initial_pred1 = extract_answer(initial_response1)
    initial_pred2 = extract_answer(initial_response2)
    return pred1, pred2, initial_pred1, initial_pred2


def single_request(client, single_question, cot_examples_dict, exist_results, log_dir:Path=None, retake:bool=False):
    exist = True
    q_id = single_question["question_id"]
    result = exist_results.get(q_id)
    if result is not None:
        if single_question["question"] == result["question"] and not retake:
            final_response1 = result["model_outputs"][0]
            final_response2 = result["model_outputs"][1]
            initial_response1 = result["init_outputs"][0]
            initial_response2 = result["init_outputs"][1]
            pred1, pred2, initial_pred1, initial_pred2 = get_answers(final_response1=final_response1, final_response2=final_response2, initial_response1=initial_response1, initial_response2=initial_response2)
            return (pred1, pred2), (final_response1, final_response2), (initial_pred1, initial_pred2), (initial_response1, initial_response2), exist
    exist = False
    category = single_question["category"]
    cot_examples = cot_examples_dict[category]
    prompt = build_prompt(category, cot_examples)
    question = single_question["question"]
    options = single_question["options"]
    input_text = format_example(question, options, "from user")
    try:
        log_filename = f"Question#{q_id}.md"
        print(f"Question#{q_id} being attempted")
        final_response1, final_response2, initial_response1, initial_response2 = call_api(client, prompt, input_text, log_dir=log_dir, log_filename=log_filename)
        pred1, pred2, initial_pred1, initial_pred2 = get_answers(final_response1=final_response1, final_response2=final_response2, initial_response1=initial_response1, initial_response2=initial_response2)
        print(f"Question#{q_id} answered. Consensus: {pred1 == pred2}")
        return (pred1, pred2), (final_response1, final_response2), (initial_pred1, initial_pred2), (initial_response1, initial_response2), exist
    except Exception as e:
        print("error", e)
        return None, None, None, None, exist


def load_results(filepath):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump({}, f, indent=2)
            data = {}
    else:
        with open(filepath, 'r') as f:
            data = json.load(f)
    return {item['question_id']: item for item in data}


def save_results(filepath, results):
    # Convert the dictionary to a list of dictionaries
    output_data = list(results.values()) 

    with open(filepath, 'w') as f:
        json.dump(output_data, f, indent=2)


def load_summary(filepath):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump({}, f, indent=2)
            summary = {}
    else:
        with open(filepath, 'r') as f:
            summary = json.load(f)
    return summary


def save_summary(filepath, summary):
    """
    Save summary to JSON file with 'overall' key first, followed by other subject keys in alphabetical order.
    Internal dictionary structure remains unchanged.
    
    Args:
        filepath: Path to save the JSON file
        summary: Dictionary containing the summary data
    """
    # Create new OrderedDict with desired order at subject level only
    sorted_summary = OrderedDict()
    
    # Add 'overall' first if it exists
    if 'overall' in summary:
        sorted_summary['overall'] = summary['overall']
    
    # Add remaining subjects in alphabetical order
    for subject in sorted(k for k in summary.keys() if k != 'overall'):
        sorted_summary[subject] = summary[subject]
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(sorted_summary, f, indent=2)


def call_api(client, prompt, input_text, log_dir: Path = None, log_filename: str = None):
    start = time.time()
    result1, result2, initial_result1, initial_result2 = client.get_response(input_text, user_instructions=prompt, log_dir=log_dir, log_filename=log_filename)
    print("cost time", time.time() - start)
    return result1, result2, initial_result1, initial_result2


def get_client():
    return DebateAPIModel(model1_name=parsed_args.model1_name, model2_name=parsed_args.model2_name)


def evaluate(subjects):
    client = get_client()
    test_df, dev_df = load_mmlu_pro()
    if not subjects:
        subjects = list(test_df.keys())
    for subject in subjects:
        test_data = test_df[subject]
        if len(test_data) > parsed_args.batch_size:
            test_data = random.sample(test_data, parsed_args.batch_size)
        output_res_path = os.path.join(parsed_args.output_dir, subject.replace(" ", "_") + "_result.json")
        results = load_results(output_res_path)

        for each in tqdm(test_data):
            category = subject
            log_dir = Path(os.path.join(parsed_args.output_dir, "answers", category))
            pred, response, init_pred, init_response, _ = single_request(client, each, dev_df, results, log_dir=log_dir)
            if response is not None:
                each["pred"] = pred
                each["init_pred"] = init_pred
                each["model_outputs"] = response
                each["init_outputs"] = init_response
                results[each["question_id"]] = each
                save_results(output_res_path, results)
        
        output_summary_path = os.path.join(parsed_args.output_dir, "results_summary.json")
        generate_summary(subject, output_summary_path, results)
        
        
def evaluate_question(question_number, subjects):
    client = get_client()
    test_df, dev_df = load_mmlu_pro()
    if not subjects:
        subjects = list(test_df.keys())
    for subject in subjects:
        test_data = test_df[subject]
        output_res_path = os.path.join(parsed_args.output_dir, subject.replace(" ", "_") + "_result.json")
        results = load_results(output_res_path)
        for each in test_data:
            if each["question_id"] == question_number:
                category = subject
                log_dir = Path(os.path.join(parsed_args.output_dir, "answers", category.replace(" ", "_")))
                pred, response, init_pred, init_response, _ = single_request(client, each, dev_df, results, log_dir=log_dir, retake=True)
                if response is not None:
                    each["pred"] = pred
                    each["init_pred"] = init_pred
                    each["model_outputs"] = response
                    each["init_outputs"] = init_response
                    results[each["question_id"]] = each
                    save_results(output_res_path, results)
        
                output_summary_path = os.path.join(parsed_args.output_dir, "results_summary.json")
                generate_summary(subject, output_summary_path, results)
                return
    print(f"Question#{question_number} not found")


def generate_summary(subject, output_summary_path, results):
    """
    Generate summary statistics for model predictions and save to file.
    Creates both subject-specific and overall summaries.
    
    Args:
        subject: Subject identifier
        output_summary_path: Path to save summary file
        results: Dictionary of prediction results
    """
    summary = load_summary(output_summary_path)
    update_summary(summary, subject, results)
    save_summary(filepath=output_summary_path, summary=summary)


def main(args=None):
    global parsed_args
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", "-o", type=str, default="eval_results/")
    parser.add_argument("--model1_name", "-m1", type=str)
    parser.add_argument("--model2_name", "-m2", type=str)
    parser.add_argument("--subjects", "-s", type=str, default="all")
    parser.add_argument("--batch_size", "-b", type=int, default=sys.maxsize)
    parser.add_argument("--question", "-q", type=int, default=-1)
    
    assigned_subjects = []
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args=args)

    if parsed_args.subjects == "all":
        assigned_subjects = []
    else:
        assigned_subjects = parsed_args.subjects.split(",")
    os.makedirs(parsed_args.output_dir, exist_ok=True)
    
    if parsed_args.question != 1:
        evaluate_question(parsed_args.question, assigned_subjects)
    else:
        evaluate(assigned_subjects)
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)