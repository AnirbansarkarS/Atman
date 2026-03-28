import os
from dotenv import load_dotenv
# You would need to install the 'anthropic' library: pip install anthropic
# from anthropic import Anthropic

load_dotenv()

# CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
# if not CLAUDE_API_KEY:
#     raise ValueError("CLAUDE_API_KEY not found in .env file")

# client = Anthropic(api_key=CLAUDE_API_KEY)

def get_response(prompt: str) -> str:
    """
    Gets a response from the Claude API.
    """
    # try:
    #     message = client.messages.create(
    #         model="claude-3-opus-20240229", # Or another model
    #         max_tokens=1024,
    #         messages=[
    #             {"role": "user", "content": prompt}
    #         ]
    #     )
    #     return message.content
    # except Exception as e:
    #     print(f"Error calling Claude API: {e}")
    #     return "Sorry, I encountered an error."
    
    # Placeholder response
    return f"This is an AI-generated response to: '{prompt}'"


if __name__ == '__main__':
    test_prompt = "Hello, who are you?"
    response = get_response(test_prompt)
    print(f"Prompt: {test_prompt}")
    print(f"Response: {response}")
