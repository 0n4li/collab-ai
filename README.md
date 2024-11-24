# Collab AI

There are so many SOTA LLM models, with their own unique strengths and weaknesses. The key idea here is to have these models work together and provide a collaborative response to user queries and get an improved response than the one obtained through any single model.

We will experiment with different strategies to achieve the best results. We are starting with a "[DebateAPIModel](src/api/debate_api_model.py)".

## Debate API Model

The Debate API Model facilitates a natural dialogue-based discussion between two AI models to generate comprehensive responses to user queries. It leverages the strengths of different models to provide well-rounded and thoroughly vetted answers.

### Features

*   **Multi-Model Discussion:** Employs two distinct AI models (e.g., OpenAI's GPT-4o and Google's Gemini-Flash) to engage in a debate or discussion.
*   **Natural Dialogue Simulation:** Prompts are designed to mimic natural conversation, enabling models to respond, critique, and refine each other's perspectives.
*   **Agreement Tracking:** Monitors agreement status between models throughout the discussion to determine when convergence is reached.
*   **Comprehensive Responses:** Synthesizes a final answer that integrates insights from both models, considering agreements, disagreements, and clarifications.
*   **Configurable User Instructions:** Allows users to provide specific instructions to guide the debate and tailor the final response.
*   **Conversation Logging:** Captures the entire debate transcript, including individual model responses, agreement statuses, and the final synthesized answer for analysis and auditing.

### Setup

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/0n4li/collab-ai.git
    cd src
    ```

2. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure .env File:**

    *   A sample `.env.example` file has been provided. Copy that using the below command:

    ```bash
    cp .env.example .env
    ```
    *   Update values for `ROUTER_BASE_URL` and `ROUTER_API_KEY` in the `.env` file. Any OpenAI Compatible API may be used.

    ```sh
    # Use any OpenAI Compatible provider
    ROUTER_BASE_URL=https://openrouter.ai/api/v1/
    ROUTER_API_KEY=YOUR-OPEN-ROUTER-KEY-HERE

    # Optional
    VERIFY_SSL=True
    ```

### Usage

#### Basic Usage

```bash
python run_debate_model.py --question "How many 'r's are there in strawberry?" --user_instructions "Break all the letters, index only the 'r's and return the count" -c "r-in-strawberry"
```

```python
from pathlib import Path
from debate_api_model import DebateAPIModel

# Initialize the debate model with the names of the two models you want to use
debate_model = DebateAPIModel(
    model1_name="openai/gpt-4o-mini",
    model2_name="google/gemini-flash-1.5",
    user_instructions="Engage in thoughtful discussion with focus on understanding and truth-seeking."
)

# Specify the user question and any additional instructions
user_question = "What is the most efficient sorting algorithm for large datasets?"
user_instructions = "Focus on time complexity and practical applications."
log_dir = Path("./logs") # Specify the directory to save logs
log_filename = "debate_log"

# Get the response through natural discussion between models
response = debate_model.get_response(user_question, user_instructions, log_dir, log_filename)

# Print the final responses
print("\nModel 1 Collaborative Response:", response[0])
print("\nModel 2 Collaborative Response:", response[1])
print("\nModel 1 Initial Response:", response[2])
print("\nModel 2 Initial Response:", response[3])

# Close the model conversations
debate_model.close()
```

### Customization

*   **Model Selection:**
    *   Change the `model1_name` and `model2_name` arguments in the `DebateAPIModel` constructor to use different AI models.
    *   Ensure that the models you specify are supported by your API setup.

    ```python
    debate_model = DebateAPIModel(
        model1_name="openai/gpt-3.5-turbo",
        model2_name="another-model/api",
        ...
    )
    ```
*   **User Instructions:**
    *   Provide specific instructions to guide the debate using the `user_instructions` argument in the `get_response` method.

    ```python
    user_instructions = "Focus on providing examples and counter-examples."
    response = debate_model.get_response(user_question, user_instructions)
    ```
*   **Logging:**
    *   The conversation logs will be saved in the specified directory or the default logs directory. The logs will be saved in separate files for each conversation and will include the model names in the log file.
    *   The individual model and collaborative responses can be accessed and used as needed:
        ```python
         # Get the response through natural discussion between models
            response = debate_model.get_response(user_question, user_instructions, log_dir, log_filename)

        # Print the final responses
            print("\nModel 1 Collaborative Response:", response[0])
            print("\nModel 2 Collaborative Response:", response[1])
            print("\nModel 1 Initial Response:", response[2])
            print("\nModel 2 Initial Response:", response[3])
        ```

## API Model

The `APIModel` class in `api_model.py` is a wrapper for interacting with different AI model APIs. It supports:

*   Starting and closing conversations.
*   Sending messages and receiving responses.
*   Handles API-specific configurations (you may need to extend it for new model APIs).

    *   Currently supports Google and Open AI models.

## Prompts

The `prompts.py` file contains various prompt templates used for different stages of the debate:

*   **System Prompt (`system_prompt`)**: Sets the overall behavior and goals for the models.
*   **Initial Response Prompt (`initial_response_prompt`)**: Asks models for their initial perspective on the user question.
*   **Perspective Prompt (`perspective_prompt`)**: Presents one model's perspective to the other.
*   **Discussion Prompt (`discussion_prompt`)**: Asks models to critique or respond to another model's input.
*   **Perspective and Discussion Prompt (`perspective_and_discussion_prompt`)**: Combines perspective presentation and discussion request.
*   **Final Answer Prompt (`final_answer_prompt`)**: Asks models for their final answer after the discussion.
*   **Final Response Prompts (`final_response_prompt_agreement`, `final_response_prompt_disagreement`)**: Used to generate the final response based on the agreement status.

## Logging Configuration

The `logging_config.py` file sets up logging for both the application and individual conversations. It provides:

*   **Application Logger:** Logs general application events.
*   **Conversation Logger:** Logs detailed transcripts of each conversation.
*   A no-op logger for cases where logging is not desired.

## Extract Pattern

The `extract_pattern.py` file contains a function to extract agreement status from model responses.

## Project Structure

```
debate-api-model/
├── api/
│   ├── api_model.py         # API interaction wrapper
│   ├── extract_pattern.py   # Agreement status extraction
│   ├── logging_config.py    # Logging setup
│   ├── prompts.py           # Prompt templates
│   └── __init__.py
├── debate_api_model.py    # Main Debate API Model class
├── requirements.txt       # Project dependencies
├── README.md              # This file
└── .env                   # API keys and other env vars
```

## Future Enhancements

*   Support for more AI models and APIs.
*   Advanced agreement/disagreement detection.
*   Summarization of discussion points.
*   Web interface/API endpoint for easier interaction.
*   Configurable debate parameters (number of rounds, etc.).
*   Automatic evaluation metrics to assess response quality.

## Contributing

Feel free to fork the project, create a new branch, make your changes and create a pull request. Please adhere to standard coding practices and include tests where appropriate.


# Collab AI

## Sample Run Command for MMLU PRO

### Random Question

    python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s business -b 1 -o 4o-mini--flash-1-5

### Specific Question

    python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s physics -q 9206 -o 4o-mini--flash-1-5