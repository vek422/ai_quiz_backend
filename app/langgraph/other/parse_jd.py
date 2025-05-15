from app.langgraph.prompts import jd_parsing_prompt
from app.core.config import llm
import json


def parse_jd(jd_text: str) -> dict:
    """
    Parse the job description text using OpenAI's GPT-4o model.
    """
    # Prepare the prompt
    prompt = jd_parsing_prompt.format(jd_text=jd_text)

    # Call the OpenAI API
    response = llm.invoke(prompt)

    # Extract the parsed data from the response
    response_text = response.content

    # we have to return the string version of the json object
    # Parse the JSON response
    try:
        parsed_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    # Return the parsed data
    return json.dumps(parsed_data)
