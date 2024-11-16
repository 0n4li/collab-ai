from typing import Optional
import re
import hashlib
from pathlib import Path

from api.prompts import system_prompt, initial_response_prompt, perspective_prompt, discussion_prompt, perspective_and_discussion_prompt, final_response_prompt
from api.api_model import APIModel
from api.logging_config import setup_app_logger, setup_conversation_logger

# Set up application logger
logger = setup_app_logger(__name__)

class DebateAPIModel:
    def __init__(self, model1_name: str, model2_name: str, user_instructions: str):
        """
        Initialize two AI models for natural dialogue-based discussion.

        Args:
            model1_name: Name of the first model
            model2_name: Name of the second model
            user_instructions: Base instructions for the models
        """
        self.user_instructions = user_instructions
        self.debate_prompt = system_prompt.format(user_instructions)
        self.initial_response_prompt = initial_response_prompt
        self.perspective_prompt = perspective_prompt
        self.discussion_prompt = discussion_prompt
        self.perspective_and_discussion_prompt = perspective_and_discussion_prompt
        self.final_response_prompt = final_response_prompt
        
        self.model1 = APIModel(model=model1_name, system_prompt=self.debate_prompt)
        self.model2 = APIModel(model=model2_name, system_prompt=self.debate_prompt)
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.max_discussion_rounds = 5  # Maximum number of discussion rounds
        
        logger.info(f"DebateAPIModel initialized with {model1_name} and {model2_name}")

    def _setup_conversation_logger(self, log_dir: Path=None, log_filename: str=None):
        """Set up a new logger for the current conversation."""
        return setup_conversation_logger(self.model1_name, self.model2_name, log_dir=log_dir, log_filename=log_filename)

    def _format_initial_response_prompt(self, user_question: str) -> str:
        return self.initial_response_prompt.format(user_question)
    
    def _format_perspective_prompt(self, perspective: str) -> str:
        return self.perspective_prompt.format(perspective)
    
    def _format_discussion_prompt(self, discussion_point: str) -> str:
        return self.discussion_prompt.format(discussion_point)
    
    def _format_perspective_and_discussion_prompt(self, perspective: str, discussion_point: str) -> str:
        return self.perspective_and_discussion_prompt.format(perspective, discussion_point)
    
    def _format_final_response_prompt(self, user_question: str, transcript: str) -> str:
        return self.final_response_prompt.format(user_question, transcript, self.user_instructions)
    
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

    def get_response(self, user_question: str, log_dir: Path = None, log_filename: str = None) -> str:
        """
        Get response through natural discussion between models.

        Args:
            user_question: The question to be answered

        Returns:
            Final synthesized response
        """
        
        transcript = f"User Question:\n\n{user_question}\n\n"
        
        conv_logger = self._setup_conversation_logger(log_dir=log_dir, log_filename=log_filename)
        conv_logger.info(f"## User Question\n")
        conv_logger.info(f"{user_question}\n")
        conv_logger.info(f"---\n")
        print("User Question:\n", user_question, "\n")

        self.start()

        # Initial perspectives
        print(f"Getting initial Response from {self.model1_name}")
        model1_initial_response = self.model1.send_message(self._format_initial_response_prompt(user_question))
        conv_logger.info(f"### {self.model1_name} Initial Response:\n")
        conv_logger.info(f"{model1_initial_response}\n")
        conv_logger.info(f"---\n")
        print(f"{self.model1_name} gave an initial response")
        
        transcript+=f"Model 1 Initial Response:\n\n{model1_initial_response}\n\n"

        print(f"Getting initial Response from {self.model2_name}")
        model2_initial_response = self.model2.send_message(self._format_discussion_prompt(user_question))
        conv_logger.info(f"### {self.model2_name} Initial Response:\n")
        conv_logger.info(f"{model2_initial_response}\n")
        conv_logger.info(f"---\n")
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
            conv_logger.info(f"### {self.model1_name} Discussion Response Round {current_round + 1}:\n{model1_response_discussion}\n")
            conv_logger.info(f'\n---\n\n')
            transcript+=f"Model 1 Discussion Round {(current_round + 1)}:\n\n{model1_response_discussion}\n\n"

            # Check Model 1's agreement status
            status1 = self._check_agreement_status(model1_response_discussion)
            print(f"{self.model1_name} agreement status - {status1} - after round {current_round + 1}")
            
            # Model 2 responds to Model 1's analysis
            model2_response_discussion = self.model2.send_message(
                self._format_perspective_and_discussion_prompt(model1_initial_response, model1_response_discussion) if current_round == 0 else
                self._format_discussion_prompt(model1_response_discussion)
            )
            conv_logger.info(f"### {self.model2_name} Discussion Response Round {current_round + 1}:\n{model2_response_discussion}\n")
            conv_logger.info(f'\n---\n\n')
            transcript+=f"Model 2 Discussion Round {(current_round + 1)}:\n\n{model2_response_discussion}\n\n"

            # Check Model 2's agreement status
            status2 = self._check_agreement_status(model2_response_discussion)
            print(f"{self.model2_name} agreement status - {status2} - after round {current_round + 1}")

            # Update agreement status based on both models' responses
            if status1 == "agree" and status2 == "agree":
                agreement_status = "agree"
                break
            
            current_round += 1

        conv_logger.info(f"*Agreement Status*: {agreement_status} - Model 1 ({status1}) / Model 2 ({status2})")
        conv_logger.info(f'\n---\n\n')
        print(f"Agreement status: {agreement_status} - Model 1 ({status1}) / Model 2 ({status2})")

        self.restart()
        
        conv_logger.info(f"*Full transcript*:\n\n{transcript}\n")
        conv_logger.info(f'\n---\n\n')
        print(f"*Full transcript*:\n\n{transcript}\n")
        
        final_response_prompt = self._format_final_response_prompt(user_question, transcript)
        
        model1_final_response = self.model1.send_message(final_response_prompt)
        conv_logger.info(f"## {self.model1_name} Collaborative Answer:\n\n{model1_final_response}\n")
        print(f"{self.model1_name} collaborative answer received")

        model2_final_response = self.model2.send_message(final_response_prompt)
        conv_logger.info(f"## {self.model2_name} Collaborative Answer:\n\n{model2_final_response}\n")
        print(f"{self.model2_name} collaborative answer received")

        # Close the conversation logger
        for handler in conv_logger.handlers[:]:
            handler.close()
            conv_logger.removeHandler(handler)

        return model1_final_response, model2_final_response, model1_initial_response, model2_initial_response

    def start(self):
        """Start conversations for both models."""
        self.model1.start_conversation()
        self.model2.start_conversation()

    def close(self):
        """Close conversations for both models."""
        self.model1.close_conversation()
        self.model2.close_conversation()
        
    def restart(self):
        self.close()
        self.start()


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
