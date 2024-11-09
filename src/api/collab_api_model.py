import logging
import re
import os
from typing import List
from datetime import datetime

from api.api_model import APIModel
from api.system_prompt import prompt_generator

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
os.makedirs("src/logs", exist_ok=True)


class CollabAPIModel:
    def __init__(self, model1_name: str, model2_name: str, user_instructions: str):
        """
        Initialize two collaborative AI models.

        Args:
            model1_name: Name of the first model
            model2_name: Name of the second model
            user_instructions: Instructions used to create system prompt
        """
        self.system_prompt = prompt_generator.generate_prompt(user_instructions)
        self.model1 = APIModel(model=model1_name, system_prompt=self.system_prompt)
        self.model2 = APIModel(model=model2_name, system_prompt=self.system_prompt)
        self.model1_name = model1_name
        self.model2_name = model2_name
        self.consensus_history = []
        logger.info(f"CollabAPIModel initialized with {model1_name} and {model2_name}")

    def _setup_conversation_logger(self):
        """Set up a new logger for the current conversation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversation_logger = logging.getLogger(f"conversation_{timestamp}")
        conversation_logger.setLevel(logging.INFO)

        # Create a new file handler for this conversation
        log_file = f"src/logs/conversation_{timestamp}.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        conversation_logger.addHandler(handler)

        return conversation_logger

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence percentage from model response."""
        match = re.search(r"Overall Confidence: (\d+)%", response)
        if match:
            return float(match.group(1))
        return 0.0

    def _calculate_consensus_improvement(self) -> bool:
        """
        Calculate if consensus is improving over the last 3 iterations.
        Returns True if improving or stable, False if declining.
        """
        if len(self.consensus_history) < 3:
            return True

        last_three = self.consensus_history[-3:]
        return last_three[2] >= last_three[1] >= last_three[0]

    def _get_consensus_score(self, response1: str, response2: str) -> float:
        """Calculate consensus score between two responses."""
        confidence1 = self._extract_confidence(response1)
        confidence2 = self._extract_confidence(response2)
        return (confidence1 + confidence2) / 2

    def get_response(self, user_question: str) -> str:
        """
        Get collaborative response to user question.

        Args:
            user_question: The question to be answered

        Returns:
            Final consensus response from the models
        """
        # Set up logging for this conversation
        conv_logger = self._setup_conversation_logger()
        conv_logger.info(f"New conversation started")
        conv_logger.info(f"Models: {self.model1_name} and {self.model2_name}")
        conv_logger.info(f"User Question: {user_question}\n")

        # Reset conversation and consensus history
        self.model1.start_conversation()
        self.model2.start_conversation()
        self.consensus_history = []

        # Initial responses from both models
        response1 = self.model1.send_message(user_question)
        response2 = self.model2.send_message(user_question)

        # Log initial responses
        conv_logger.info(f"{self.model1_name} Initial Response:\n{response1}\n")
        conv_logger.info(f"{self.model2_name} Initial Response:\n{response2}\n")

        iteration = 0
        max_iterations = 5

        while iteration < max_iterations:
            # Calculate consensus score
            consensus_score = self._get_consensus_score(response1, response2)
            self.consensus_history.append(consensus_score)
            conv_logger.info(
                f"Iteration {iteration + 1} - Consensus Score: {consensus_score}%\n"
            )

            # Check if consensus reached (>80%)
            if consensus_score > 80:
                final_response = (
                    response1 if len(response1) > len(response2) else response2
                )
                conv_logger.info(f"Consensus reached with score {consensus_score}%")
                conv_logger.info(f"Final Response:\n{final_response}\n")
                return final_response

            # Check if consensus is improving
            if not self._calculate_consensus_improvement() and iteration >= 2:
                final_response = (
                    response1 if len(response1) > len(response2) else response2
                )
                conv_logger.info("Consensus not improving, stopping iterations")
                conv_logger.info(f"Final Response:\n{final_response}\n")
                return final_response

            # Continue iteration by having models review each other's responses
            review_prompt = f"""Review and integrate the following response from your partner:
            {response2}
            
            Provide your updated analysis and work towards consensus."""

            response1 = self.model1.send_message(review_prompt)
            conv_logger.info(
                f"{self.model1_name} Review Response (Iteration {iteration + 1}):\n{response1}\n"
            )

            review_prompt = f"""Review and integrate the following response from your partner:
            {response1}
            
            Provide your updated analysis and work towards consensus."""

            response2 = self.model2.send_message(review_prompt)
            conv_logger.info(
                f"{self.model2_name} Review Response (Iteration {iteration + 1}):\n{response2}\n"
            )

            iteration += 1

        final_response = response1 if len(response1) > len(response2) else response2
        conv_logger.info("Max iterations reached")
        conv_logger.info(f"Final Response:\n{final_response}\n")

        # Close the conversation logger
        for handler in conv_logger.handlers[:]:
            handler.close()
            conv_logger.removeHandler(handler)

        return final_response

    def close(self):
        """Close conversations for both models."""
        self.model1.close_conversation()
        self.model2.close_conversation()


def main():
    # Example usage
    collab_model = CollabAPIModel(
        model1_name="openai/gpt-4o-mini",
        model2_name="google/gemini-flash-1.5",
        user_instructions="Provide detailed, technical responses with a focus on accuracy and consensus.",
    )

    response = collab_model.get_response("How many 's' are there in strawberry?")
    print("Collaborative Response:", response)
    collab_model.close()


if __name__ == "__main__":
    main()
