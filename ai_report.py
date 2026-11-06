
import os
import json
import time

from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()



def generate_ai_report(business_metrics):

    import os
    import json
    import time

    from dotenv import load_dotenv
    from google import genai

    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key not found.")

    print("1. Initializing Gemini client...")

    client = genai.Client(
        api_key=api_key,
        http_options={
            "timeout": 180000
        }
    )

    metrics_json = json.dumps(
        business_metrics,
        indent=4
    )

    instructions = """
    You are a senior business analyst.

    Prepare a management report with:
    1. Executive Summary
    2. Financial Performance
    3. Inventory and Waste Analysis
    4. Areas of Concern
    5. Recommended Management Actions

    Use only the supplied figures.
    Do not invent data or assume unproven causes.
    """

    prompt = f"""
    BUSINESS PERFORMANCE DATA:

    {metrics_json}

    Prepare the management report.
    """

    print("2. Sending request to Gemini...")

    start_time = time.time()

    for attempt in range(3):
        try:
            response = client.interactions.create(
                model="gemini-3.5-flash-lite",
                input=prompt,
                system_instruction=instructions
            )
            return response.output_text

        except Exception as error:
            error_message = str(error).lower()

            temporary_errors = [
                "503",
                "server disconnected",
                "connection",
                "timeout"
            ]

            is_temporary = any(
                message in error_message
                for message in temporary_errors
            )

            if is_temporary and attempt < 2:
                time.sleep(10 * (attempt + 1))
            else:
                raise

    elapsed = round(time.time() - start_time, 2)

    print(f"3. Gemini responded in {elapsed} seconds.")

    return response.output_text