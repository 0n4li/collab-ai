import argparse
import os
import json
import random
import time
import sys
from datasets import load_dataset
from tqdm import tqdm
from pathlib import Path

from api.debate_api_model import DebateAPIModel
from benchmarks.extract_answer import extract_answer

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
    example = "Question {}: {}\nOptions: ".format(question_number, question)
    choice_map = "ABCDEFGHIJ"
    for i, opt in enumerate(options):
        example += "{}. {}\n".format(choice_map[i], opt)
    if cot_content == "":
        example += "Answer: "
    else:
        example += "Answer: " + cot_content + "\n\n"
    return example


def single_request(client, single_question, cot_examples_dict, exist_results, log_dir:Path=None):
    exist = True
    q_id = single_question["question_id"]
    result = exist_results.get(q_id)
    if result is not None:
        if single_question["question"] == result["question"]:
            final_response1 = result["model_outputs"][0]
            final_response2 = result["model_outputs"][1]
            initial_response1 = result["init_outputs"][0]
            initial_response2 = result["init_outputs"][1]
            pred1 = extract_answer(final_response1)
            pred2 = extract_answer(final_response2)
            initial_pred1 = extract_answer(initial_response1)
            initial_pred2 = extract_answer(initial_response2)
            return (pred1, pred2), (final_response1, final_response2), (initial_pred1, initial_pred2), (initial_response1, initial_response2), exist
    exist = False
    category = single_question["category"]
    cot_examples = cot_examples_dict[category]
    question = single_question["question"]
    options = single_question["options"]
    prompt = "The following are multiple choice questions (with answers) about {}. Think step by" \
             " step and then output the answer in the format of \"The answer is (X)\" at the end.\n\n" \
        .format(category)
    question_number = 1
    for each in cot_examples:
        prompt += format_example(each["question"], each["options"], question_number, each["cot_content"])
        question_number += 1
    input_text = format_example(question, options, question_number)
    input_text += f"\n\nVERY IMPORTANT INSTRUCTION: In your final response only provide the analysis and answer for Question {question_number} (The earlier questions are only meant as examples of correct answers and are not to be discussed further). Always clearly state your answer as \"The answer is (X)\" at the end.\n"
    try:
        log_filename = f"Question#{q_id}.md"
        final_response1, final_response2, initial_response1, initial_response2 = call_api(client, prompt, input_text, log_dir=log_dir, log_filename=log_filename)
        pred1 = extract_answer(final_response1)
        pred2 = extract_answer(final_response2)
        initial_pred1 = extract_answer(initial_response1)
        initial_pred2 = extract_answer(initial_response2)
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
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)


def call_api(client, prompt, input_text, log_dir: Path = None, log_filename: str = None):
    start = time.time()
    message_text = prompt + input_text
    result1, result2, initial_result1, initial_result2 = client.get_response(message_text, log_dir=log_dir, log_filename=log_filename)
    print("cost time", time.time() - start)
    return result1, result2, initial_result1, initial_result2


def get_client(user_instructions=""):
    return DebateAPIModel(model1_name=parsed_args.model1_name, model2_name=parsed_args.model2_name, user_instructions=user_instructions)

def evaluate(subjects):
    client = get_client(user_instructions="When giving the final response, present your analysis and answer the question as `The answer is (X)` at the end.")
    test_df, dev_df = load_mmlu_pro()
    if not subjects:
        subjects = list(test_df.keys())
    for subject in subjects:
        test_data = test_df[subject]
        if len(test_data) > parsed_args.samples_per_subject:
            test_data = random.sample(test_data, parsed_args.samples_per_subject)
        output_res_path = os.path.join(parsed_args.output_dir, subject + "_result.json")
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


def generate_summary(subject, output_summary_path, results):
    summary = load_summary(output_summary_path)    
    subject_summary = {}
    corr = 0
    wrong = 0
    acc = 0
    for each in list(results.values()):
        if each["pred"] is not None:
            if each["pred"][0] == each["answer"] and each["pred"][1] == each["answer"]:
                corr += 1
            elif each["pred"][0] == each["answer"] or each["pred"][1] == each["answer"]:
                corr += 0.5
                wrong += 0.5
            else:
                wrong += 1
    total = corr + wrong
    acc = "NA" if total == 0 else corr / total
    subject_summary['corr'] = corr
    subject_summary['wrong'] = wrong
    subject_summary['acc'] = acc
    summary[subject] = subject_summary
    save_summary(filepath=output_summary_path, summary=summary)


def main(args=None):
    global parsed_args
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", "-o", type=str, default="eval_results/")
    parser.add_argument("--model1_name", "-m1", type=str)
    parser.add_argument("--model2_name", "-m2", type=str)
    parser.add_argument("--assigned_subjects", "-a", type=str, default="all")
    parser.add_argument("--samples_per_subject", "-s", type=int, default=sys.maxsize)
    assigned_subjects = []
    if args is None:
        args = sys.argv[1:]
    parsed_args = parser.parse_args(args=args)

    if parsed_args.assigned_subjects == "all":
        assigned_subjects = []
    else:
        assigned_subjects = parsed_args.assigned_subjects.split(",")
    os.makedirs(parsed_args.output_dir, exist_ok=True)
    evaluate(assigned_subjects)
    
if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)