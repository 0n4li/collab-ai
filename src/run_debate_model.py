from api.debate_api_model import DebateAPIModel

def main():
    # Test question and user instructions
    test_question = "Let V be the set of all real polynomials p(x). Let transformations T, S be defined on V by T:p(x) -> xp(x) and S:p(x) -> p'(x) = d/dx p(x), and interpret (ST)(p(x)) as S(T(p(x))). Which of the following is true? "
    answer_options = [ "ST + TS is the identity map of V onto itself.", "TS = 0", "ST = 1", "ST - TS = 0", "ST = T", "ST = 0", "ST = TS", "ST - TS is the identity map of V onto itself.", "TS = T", "ST = S" ]
    user_instructions = "Let's think step by step."
    
    # Initialize the debate model with two different AI models
    
    debate_model = DebateAPIModel(
        model1_name="openai/gpt-4o-mini",
        model2_name="google/gemini-flash-1.5",
        user_instructions=user_instructions
    )
    
    test_question = f"{test_question} {answer_options}"

    # Test question that could have different perspectives
    print(f"\nQuestion: {test_question}")
    print("\nThinking...\n")
    
    # Get response and ensure we only print the first occurrence
    full_response = debate_model.get_response(test_question)
    
    # Split on any duplicate content by finding where the content starts repeating
    response_parts = full_response.split('\n\n')
    seen = set()
    unique_parts = []
    
    for part in response_parts:
        if part.strip() and part not in seen:
            seen.add(part)
            unique_parts.append(part)
    
    print('\n\n'.join(unique_parts))
    
    debate_model.close()

if __name__ == "__main__":
    main()
