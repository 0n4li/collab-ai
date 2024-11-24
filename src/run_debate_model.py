import argparse
import sys
from api.debate_api_model import DebateAPIModel

tempt = "Break the individual letters, index only the 'r's, and count."

default_user_instructions = "Think step by step and provide a helpful response"
default_model1_name = "openai/gpt-4o-mini"
default_model2_name = "google/gemini-flash-1.5"


def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Run Debate API Model Script')
    parser.add_argument("--output_dir", "-o", type=str, default="example_results/")
    parser.add_argument("--conversation_name", "-c", type=str, default=None)
    parser.add_argument("--model1_name", "-m1", type=str, default=default_model1_name)
    parser.add_argument("--model2_name", "-m2", type=str, default=default_model2_name)
    parser.add_argument("--question", "-q", type=str, required=True)
    parser.add_argument("--user_instructions", "-u", type=str, default=default_user_instructions)
    
    if args is None:
        args = sys.argv[1:]
    return parser.parse_args(args=args)
    

def main(args=None):
    
    # Parse the arguments
    args = parse_args(args)
    
    # Initialize the debate model with two different AI models
    debate_model = DebateAPIModel(
        model1_name=args.model1_name,
        model2_name=args.model2_name
    )
    
    # Test question that could have different perspectives
    print(f"Question: {args.question}")
    if args.user_instructions != default_user_instructions:
        print(f"User Instructions: {args.user_instructions}")
    
    # Get response and ensure we only print the first occurrence
    full_response = debate_model.get_response(
        args.question, 
        user_instructions=args.user_instructions, 
        log_dir=None if args.conversation_name is None else args.output_dir,
        log_filename=None if args.conversation_name is None else f"{args.conversation_name}.md"
    )
    
    # Print the response to console if not logged
    if args.conversation_name is None:
        print(f"="*50)
        print(f"1. {args.model1_name} Response: ")
        print(full_response[0])
        print(f"-"*50)
        print(f"2. {args.model2_name} Response: ")
        print(full_response[1])
        print(f"="*50)
    
    # Close the model
    debate_model.close()

if __name__ == "__main__":
    args = sys.argv[1:]
    main()
