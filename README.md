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

_Please Note_: It is possible that the two models do not reach a consensus on a topic and choose to return different answers. Also, different runs for the same question and user instructions may return different answers.


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

    A sample `.env.example` file has been provided. Copy that using the below command:

    ```bash
    cp .env.example .env
    ```
    Update values for `ROUTER_BASE_URL` and `ROUTER_API_KEY` in the `.env` file. (Any OpenAI Compatible API may be used)

    ```bash
    # Use any OpenAI Compatible provider
    ROUTER_BASE_URL=https://openrouter.ai/api/v1/
    ROUTER_API_KEY=YOUR-API-KEY-HERE

    # Optional
    VERIFY_SSL=True
    ```

### Usage

#### Basic Usage

```bash
python run_debate_model.py --question "How many 'r's are there in strawberry?" --user_instructions "Break all the letters, index only the 'r's and return the count" -c "r-in-strawberry"
```

In the above usage, default models `openai/gpt-4o-mini` and `google/gemini-flash-1.5` are used.

**Below are a few sample outputs:**
*   [r-in-strawberry.md](example_results/r-in-strawberry.md): Initially `google/gemini-flash-1.5` gives an incorrect count of the 'r's. However, it is corrected by `openai/gpt-4o-mini`. Eventually, both return the correct answer.
*   [r-in-mulbrerry.md](example_results/r-in-mullberry.md): Initially `openai/gpt4o-mini` gives an incorrect count of the 'r's by assuming the word `mulberry`. However, it is corrected by `google/gemini-flash-1.5` that the word is `mulbrerry`. Eventually, both return the correct answer.
*   [s-in-strawberry.md](example_results/s-in-strawberry.md): Both models return the correct answer initially and in collaboration as well.

_Please Note_: The `user_instructions` play a very important role in the outcome.

**Below are the supported parameters:**
1. `--question` or `-q`: The question to be asked to the model
2. `--user_instructions` or `-u`: (Optional) This acts like a system prompt
3. `--model1_name` or `-m1`: (Optional) The name of the first model. Default `openai/gpt-4o-mini`
4. `--model2_name` or `-m2`: (Optional) The name of the second model. Default `google/gemini-flash-1.5`
5. `--output_dir` or `-o`: (Optional) The directory in which to store the transcript of the conversation. Default `../example_results/`
6. `--conversation_name` or `-c`: (Optional) If you want to store the transcript as a `.md` file, the name of the transcript. If none provided, the conversation is not stored.


#### Advanced Usage

```python
from pathlib import Path
from debate_api_model import DebateAPIModel

# Initialize the debate model with the names of the two models you want to use
debate_model = DebateAPIModel(
    model1_name="openai/gpt-4o-mini", #Any supported model can be used
    model2_name="google/gemini-flash-1.5", #Any supported model can be used
    min_rounds=2, #Minimum rounds of discussion (Optional)
    max_rounds=5, #Maximum rounds of discussion (Optional)
)

# Specify the user question and any additional instructions
user_question = "What is the most efficient sorting algorithm for large datasets?"
user_instructions = "Focus on time complexity and practical applications."
log_dir = Path("./logs") # Specify the directory to save logs (Optional)
log_filename = "debate_log" # Specify the name of the log file (Optional)

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

## Benchmarks

### MMLU Pro

We ran the `DebateAPIModel` on 364 random questions from [MMLU-Pro dataset](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro). Below are the results:


|                  |                | **Debate AI**  |            |   **GPT 4o-mini**   |      | **Gemini Flash 1.5**   |   |
|------------------|----------------|:------------:|:------------:|:-----------:|:------------:|:-----------:|:------------:|
| **Subject**      | **Questions**  | **Correct**  | **Accuracy** | **Correct** | **Accuracy** | **Correct** | **Accuracy** |
| **overall**      |       **364**  |   **263**    | **72.3%**    |   **243**   | **66.8%**    |   **239**   | **65.7%**    |
| biology          |            32  |        29    | 90.6%        |      27     | 84.4%        |      27     | 84.4%        |
| business         |            32  |        26    | 81.2%        |      23     | 71.9%        |      25     | **78.1%**    |
| chemistry        |            31  |        25    | 80.6%        |      20     | 64.5%        |      24     | **77.4%**    |
| computer science |            17  |        15    | 88.2%        |      14     | 82.4%        |      14     | 82.4%        |
| economics        |            28  |        23    | 82.1%        |      22     | **78.6%**    |      21     | 75.0%        |
| engineering      |            17  |        10    | 58.8%        |       7     | 41.2%        |       9     | **52.9%**    |
| health           |            32  |        22    | 68.8%        |      20     | **62.5%**    |      18     | 56.2%        |
| history          |            30  |        20    | 66.7%        |      20     | **66.7%**    |      17     | 56.7%        |
| law              |            31  |         8    | 25.8%        |       8     | 25.8%        |       9     | **29.0%**    |
| math             |            17  |        16    | 94.1%        |      17     | **100.0%**   |      15     | 88.2%        |
| other            |            32  |        24    | 75.0%        |      23     | **71.9%**    |      21     | 65.6%        |
| philosophy       |            17  |         8    | 47.1%        |       8     | **47.1%**    |       7     | 41.2%        |
| physics          |            17  |        13    | 76.5%        |      11     | 64.7%        |      11     | 64.7%        |
| psychology       |            31  |        24    | 77.4%        |      23     | **74.2%**    |      21     | 67.7%        |


*   The transcripts of all the 364 questions can be found [here](mmlu-pro--4o-mini--flash-1-5/answers/).
*   The detailed statistics can be found [here](mmlu-pro--4o-mini--flash-1-5/results_summary.json).
*   _Please Note_: Some questions were re-taken as we improved the prompts.

**Below are some samples:**

*   [Question#2893.md](mmlu-pro--4o-mini--flash-1-5/answers/biology/Question%232893.md): In this `biology` question example, `gpt-4o-mini` correctly identified the flaws in `gemini-flash-1.5` reasoning and guided towards the correct answer. Check the transcript [evaluation](mmlu-pro--4o-mini--flash-1-5/evaluations/Question%232893.md) by Claude 3.5 Sonnet.
*   [Question#9342.md](mmlu-pro--4o-mini--flash-1-5/answers/physics/Question%239342.md): In this `physics` question example, `gpt-4o-mini` tried to convince `gemini-flash-1.5` through incorrect/shallow calculations, but `gemini-flash-1.5` remained firm on its reasoning and guided towards the correct answer. Check the transcript [evaluation](mmlu-pro--4o-mini--flash-1-5/evaluations/Question%239342.md) by Claude 3.5 Sonnet.
*   [Question#4342.md](mmlu-pro--4o-mini--flash-1-5/answers/chemistry/Question%234342.md): In this `chemistry` question example, both models were incorrect in their initial calculations and arrived at different answers, however, after the discussion, they both arrived at the correct answer. Check the transcript [evaluation](mmlu-pro--4o-mini--flash-1-5/evaluations/Question%234342.md) by Claude 3.5 Sonnet.

_Please Note_: I have relied on Claude 3.5 Sonnet for evaluating certain transcripts above. However, expert opinion is welcome.

_Further Note_: There are examples where models correctly arrived at the answer, however, their methodology was incorrect. Also, for some questions, the models return different answers during different runs.

#### Sample Run Command for MMLU PRO

##### Ask a Random Question

```bash
python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s business -b 1 -o mmlu-pro--4o-mini--flash-1-5
```

*   This will ask a random question from `business` category.
*   Supported categories can be checked from MMLU-Pro dataset. (There are 14 currently)
*   Use `-b` parameter for multiple questions.
*   Use `-s all` for answering a random question(s) from all categories. 

##### Ask a Specific Question

```bash
python src/run_mmlu_pro.py -m1 openai/gpt-4o-mini -m2 google/gemini-flash-1.5 -s physics -q 9206 -o mmlu-pro--4o-mini--flash-1-5
```

*   This will ask a specific question based on `physics` category and question number `9206`
*   List of questions can be found from MMLU-Pro dataset.

## Future Enhancements

*   Support for more methodologies for collaboration.
*   Support for followup questions.
*   Web interface/API endpoint for easier interaction.
*   Run on more benchmarks like LiveBench.


## Limitations

This approach doesn't magically improve the underlying models. If the models are themselves limited in their own understanding of the topic at hand, most likely the collaborative answer will also be incorrect. Sometimes a model returns the correct answer, but using incorrect logic. It gets highlighted through the discussion and the model gets confused and is no longer able to stay firm on the original answer.

Also, sometimes the models return different answer, when re-taking the same question and user instructions.


## Contributing

Feel free to fork the project, create a new branch, make your changes and create a pull request. Please adhere to standard coding practices and include tests where appropriate.
