import os
import re


class SystemPromptGenerator:
    def __init__(self, base_prompt, protected_sections=None):
        """
        Initialize the SystemPromptGenerator with a base prompt and protected sections.

        :param base_prompt: The main system prompt to use.
        :param protected_sections: A list of section headers that should not be modified by user instructions.
        """
        self.base_prompt = base_prompt
        self.protected_sections = protected_sections if protected_sections else []

    def sanitize_user_instruction(self, instruction):
        """
        Validate and sanitize user instruction to ensure it doesn't conflict with the base prompt.

        :param instruction: User-provided additional instruction for the system prompt.
        :return: Sanitized user instruction if it passes checks, otherwise raises ValueError.
        """
        # Disallow keywords that may suggest overriding core parts of the prompt
        forbidden_patterns = ["override", "ignore", "replace", "modify"]
        if any(
            re.search(rf"\b{pattern}\b", instruction, re.IGNORECASE)
            for pattern in forbidden_patterns
        ):
            raise ValueError("Error: Instruction contains restricted keywords.")

        # Check if instruction attempts to modify protected sections
        if any(section in instruction for section in self.protected_sections):
            raise ValueError(
                "Error: Instruction cannot modify protected sections of the prompt."
            )

        # Markdown-safe handling
        if "`" in instruction:
            return f"`{instruction}`"

        return instruction

    def generate_prompt(self, user_instruction):
        """
        Generate the final system prompt with sanitized user instructions.

        :param user_instruction: The additional instruction provided by the user.
        :return: Final system prompt with user instructions incorporated.
        """

        try:
            # Sanitize the user instruction
            sanitized_instruction = self.sanitize_user_instruction(user_instruction)
        except ValueError as e:
            sanitized_instruction = "You are a helpful assistant."

        # Insert the sanitized instruction into the prompt
        final_prompt = self.base_prompt.replace(
            "%%ADDITIONAL_USER_INSTRUCTION%%", sanitized_instruction
        )

        return final_prompt


# Read the base prompt from the markdown file
def load_base_prompt(file_path="base_prompt.md"):
    with open(file_path, "r") as file:
        return file.read()


# Get the full path of the current file
current_file_path = os.path.abspath(__file__)

# Get the directory of the current file
current_directory = os.path.dirname(current_file_path)

# Load the base prompt
base_prompt = load_base_prompt(
    file_path=os.path.join(current_directory, "base_prompt.md")
)

protected_sections = [
    "## Response Format",
    "## Consensus Requirements",
    "## Iteration Guidelines",
]

# Instantiate the SystemPromptGenerator with the base prompt and protected sections
prompt_generator = SystemPromptGenerator(base_prompt, protected_sections)
