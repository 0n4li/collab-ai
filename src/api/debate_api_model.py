from pathlib import Path

from api.prompts import system_prompt, initial_response_prompt, perspective_prompt, discussion_prompt, perspective_and_discussion_prompt, final_response_prompt_agreement, final_response_prompt_disagreement
from api.api_model import APIModel
from api.logging_config import setup_app_logger, setup_conversation_logger, setup_noop_logger

# Set up application logger
logger = setup_app_logger(__name__)
separater = "\n---\n\n"

class DebateAPIModel:
    def __init__(self, model1_name: str, model2_name: str):
        """
        Initialize two AI models for natural dialogue-based discussion.

        Args:
            model1_name: Name of the first model
            model2_name: Name of the second model
        """
        self.user_instructions = ""
        self.model1 = APIModel(model=model1_name)
        self.model2 = APIModel(model=model2_name)
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.max_discussion_rounds = 5  # Maximum number of discussion rounds
        
        logger.info(f"DebateAPIModel initialized with {model1_name} and {model2_name}")

    def _setup_conversation_logger(self, log_dir: Path=None, log_filename: str=None):
        """Set up a new logger for the current conversation."""
        if log_filename is None:
            return setup_noop_logger()
        self.conv_logger = setup_conversation_logger(self.model1_name, self.model2_name, log_dir=log_dir, log_filename=log_filename)

    def _close_conversation_logger(self):
        """Close the current conversation logger."""
        if self.conv_logger:
            # Close the conversation logger
            for handler in self.conv_logger.handlers[:]:
                handler.close()
                self.conv_logger.removeHandler(handler)
                self.conv_logger = None

    def _format_initial_response_prompt(self, user_question: str) -> str:
        return initial_response_prompt.format(user_question)
    
    def _format_perspective_prompt(self, perspective: str) -> str:
        return perspective_prompt.format(perspective)
    
    def _format_discussion_prompt(self, discussion_point: str) -> str:
        return discussion_prompt.format(discussion_point)
    
    def _format_perspective_and_discussion_prompt(self, perspective: str, discussion_point: str) -> str:
        return perspective_and_discussion_prompt.format(perspective, discussion_point)
    
    def _format_final_response_prompt(self, user_question: str, transcript: str, agreement_status: str) -> str:
        if agreement_status == "agree":
            return final_response_prompt_agreement.format(user_question, transcript, self.user_instructions)
        else:
            return final_response_prompt_disagreement.format(user_question, transcript, self.user_instructions)
    
    def _check_agreement_status(self, response: str) -> str:
        """
        Check the agreement status from a model's response.
        Returns: 'agree', 'disagree', or 'unknown'
        """
        response_lower = response.lower()
        
        if "disagree" in response_lower:
            return "disagree"
        elif "agree" in response_lower:
            return "agree"
        return "unknown"
    
    def _generate_debate_prompt(_, user_instructions: str = None) -> str:
        return system_prompt.format(user_instructions)
    
    def _clog(self, message: str):
        if self.conv_logger:
            self.conv_logger.info(f"{message}\n")


    def get_response(self, user_question: str, user_instructions: str = None, log_dir: Path = None, log_filename: str = None) -> str:
        """
        Get response through natural discussion between models.

        Args:
            user_question: The question to be answered

        Returns:
            Final synthesized response
        """
        
        self._setup_conversation_logger(log_dir=log_dir, log_filename=log_filename)
        
        self._clog(f"## User Instructions")
        self._clog(user_instructions)
        self._clog(separater)
        # print(f"User Instructions:\n{user_instructions}")
        
        self._clog(f"## User Question")
        self._clog(user_question)
        self._clog(separater)
        print(f"User Question:\n{user_question}")
        
        transcript = f"User Question:\n\n{user_question}\n\n"

        debate_prompt = self._generate_debate_prompt(user_instructions)
        self.start(user_instructions=debate_prompt)

        # Initial perspectives
        print(f"Getting initial Response from {self.model1_name}")
        model1_initial_response = self.model1.send_message(self._format_initial_response_prompt(user_question))
        self._clog(f"### {self.model1_name} Initial Response:")
        self._clog(model1_initial_response)
        self._clog(separater)
        print(f"{self.model1_name} gave an initial response")
        
        transcript+=f"Model 1 Initial Response:\n\n{model1_initial_response}\n\n"

        print(f"Getting initial Response from {self.model2_name}")
        model2_initial_response = self.model2.send_message(self._format_initial_response_prompt(user_question))
        self._clog(f"### {self.model2_name} Initial Response:")
        self._clog(model2_initial_response)
        self._clog(separater)
        print(f"{self.model2_name} gave an initial response")
        
        transcript+=f"Model 2 Initial Response:\n\n{model2_initial_response}\n\n"
        
        agreement_status = "unknown"
        current_round = 0

        # Always have at least one discussion round
        while current_round < self.max_discussion_rounds:
            # Model 1 responds to Model 2's perspective
            model1_response_discussion = self.model1.send_message(
                self._format_perspective_prompt(model2_initial_response) if current_round == 0 else
                self._format_discussion_prompt(model2_response_discussion)
            )
            self._clog(f"### {self.model1_name} Discussion Response Round {current_round + 1}:")
            self._clog(model1_response_discussion)
            self._clog(separater)
            transcript+=f"Model 1 Discussion Round {(current_round + 1)}:\n\n{model1_response_discussion}\n\n"

            # Check Model 1's agreement status
            status1 = self._check_agreement_status(model1_response_discussion)
            print(f"{self.model1_name} agreement status - {status1} - after round {current_round + 1}")
            
            # Model 2 responds to Model 1's analysis
            model2_response_discussion = self.model2.send_message(
                self._format_perspective_and_discussion_prompt(model1_initial_response, model1_response_discussion) if current_round == 0 else
                self._format_discussion_prompt(model1_response_discussion)
            )
            self._clog(f"### {self.model2_name} Discussion Response Round {current_round + 1}:")
            self._clog(model2_response_discussion)
            self._clog(separater)
            transcript+=f"Model 2 Discussion Round {(current_round + 1)}:\n\n{model2_response_discussion}\n\n"

            # Check Model 2's agreement status
            status2 = self._check_agreement_status(model2_response_discussion)
            print(f"{self.model2_name} agreement status - {status2} - after round {current_round + 1}")

            # Update agreement status based on both models' responses
            if status1 == "agree" and status2 == "agree":
                agreement_status = "agree"
                break
            
            current_round += 1

        self._clog(f"## Agreement Status:")
        self._clog(f"Agreement status: {agreement_status} - Model 1 ({status1}) / Model 2 ({status2})")
        self._clog(separater)
        transcript+=f"Agreement status: {agreement_status} - Model 1 ({status1}) / Model 2 ({status2})"
        print(f"Agreement status: {agreement_status} - Model 1 ({status1}) / Model 2 ({status2})")

        self.start(user_instructions=user_instructions)
        
        # self._clog(f"## Full transcript:")
        # self._clog(transcript)
        # self._clog(separater)
        # print(f"Full transcript:\n\n{transcript}\n")
        
        final_response_prompt = self._format_final_response_prompt(user_question, transcript, agreement_status)
        
        model1_final_response = self.model1.send_message(final_response_prompt)
        self._clog(f"## {self.model1_name} Collaborative Answer:")
        self._clog(model1_final_response)
        self._clog(separater)
        print(f"{self.model1_name} collaborative answer received")

        model2_final_response = self.model2.send_message(final_response_prompt)
        self._clog(f"## {self.model2_name} Collaborative Answer:")
        self._clog(model2_final_response)
        self._clog(separater)
        print(f"{self.model2_name} collaborative answer received")

        self._close_conversation_logger()

        return model1_final_response, model2_final_response, model1_initial_response, model2_initial_response

    def start(self, user_instructions: str = None):
        self.close()
        """Start conversations for both models."""
        self.model1.start_conversation(system_prompt=user_instructions)
        self.model2.start_conversation(system_prompt=user_instructions)

    def close(self):
        """Close conversations for both models."""
        self.model1.close_conversation()
        self.model2.close_conversation()


def main():
    # Example usage
    debate_model = DebateAPIModel(
        model1_name="openai/gpt-4o-mini",
        model2_name="google/gemini-flash-1.5",
        user_instructions="Engage in thoughtful discussion with focus on understanding and truth-seeking.",
    )

    print("\nQuestion: What is the most efficient sorting algorithm for large datasets?\n")
    response = debate_model.get_response(
        "What is the most efficient sorting algorithm for large datasets?"
    )
    print("\nResponse:", response)
    debate_model.close()


if __name__ == "__main__":
    main()
