import logging
import google.generativeai as genai
import os
import json

# Set your Gemini API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Or hardcode for testing
genai.configure(api_key=GEMINI_API_KEY)

logger = logging.getLogger(__name__)

def generate_question_with_test_cases(topic, difficulty):
    # Define the prompt for generating questions
    prompt = f"""
    Generate one {difficulty} level programming question on the topic '{topic}'.
    The question should include:
    - Title
    - Description
    - 3 sample test cases with input and output in JSON format
    Return a JSON like:
    {{
        "title": "...",
        "description": "...",
        "test_cases": [
            {{"input": "...", "output": "..."}},
            ...
        ]
    }}
    """

    try:
        # Call Gemini 1.5 Flash model
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        # Gemini might return the result as plain text that needs to be parsed
        content = response.text
        logger.info(f"Received response: {content}")

        # Parse the JSON result from Gemini
        return json.loads(content)

    except Exception as e:
        logger.error(f"Error in generating question: {str(e)}")
        raise Exception(f"Gemini API Error: {str(e)}")
