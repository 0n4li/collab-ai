import os
import requests
from dotenv import load_dotenv

from api.api_request_handler import APIRequestHandler
from api.logging_config import setup_app_logger

logger = setup_app_logger(__name__)


class APIModel:
    def __init__(self, model: str):
        # Load environment variables
        load_dotenv()

        self.model = model
        self.messages = []

        self.api_base_url = os.environ.get("ROUTER_BASE_URL")
        # Ensure required environment variables are set
        if not self.api_base_url:
            raise ValueError("ROUTER_BASE_URL environment variable not set")
        
        self.api_request_handler = APIRequestHandler(self.api_base_url)

        self.api_key = os.environ.get("ROUTER_API_KEY")
        # Ensure required environment variables are set
        if not self.api_key:
            raise ValueError("ROUTER_API_KEY environment variable not set")

        logger.info("APIModel initialized.")

    def send_message(self, user_message: str) -> str:
        
        logger.info(f"Sending message to API:\n\n{user_message}\n\n")
          
        # Build the conversation payload
        self.messages.append({"role": "user", "content": user_message})
        data = {"model": self.model, "messages": self.messages, "stream": False}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            # Send synchronous request
            response_data = self.api_request_handler.make_request(
                endpoint="chat/completions",
                method="POST",
                payload=data,
                additional_headers=headers,
            )
            
            logger.info(f"Received response from API:\n\n{response_data}\n\n")

            if 'error' in response_data:
                error_info = response_data['error']
                error_code = error_info.get('code')
                error_message = error_info.get('message', 'Unknown error')
                
                # Log detailed error information for debugging
                logger.error(f"API Error - Code: {error_code}, Message: {error_message}")
                if 'metadata' in error_info:
                    logger.error(f"Error Metadata: {error_info['metadata']}")
                
                # Return a generic error message to the user
                error_response = "The service is temporarily unavailable. Please try again later."
                if error_code == 429:
                    error_response = "The service is currently experiencing high demand. Please try again in a few moments."
                
                return error_response

            assistant_message = response_data["choices"][0]["message"]["content"]
            self.messages.append({"role": "assistant", "content": assistant_message})
            return assistant_message
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network or API Request Error: {str(e)}")
            return "A network error occurred. Please check your connection and try again."
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return "An unexpected error occurred. Please try again later."

    def start_conversation(self, system_prompt: str = None):
        logger.info("Starting a new conversation.")
        self.messages = (
            [{"role": "system", "content": system_prompt}]
            if system_prompt
            else []
        )

    def close_conversation(self):
        logger.info("Closing the conversation.")
        self.messages.clear()


def main():
    user_instruction = "Provide detailed and technical responses."
    model = APIModel(model="openai/gpt-4-turbo-preview")
    model.start_conversation(system_prompt=user_instruction)
    print("Assistant Response:", model.send_message("Hello, how can you help me?"))
    model.close_conversation()


# Example usage
if __name__ == "__main__":
    main()
