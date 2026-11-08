import json
import os
import time

from dotenv import load_dotenv
from google import genai


# Load API key from .env.
load_dotenv()


def generate_ai_report(business_metrics):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("Gemini API key not found. Check your .env file.")

    print("Initializing Gemini client...")

    client = genai.Client(
        api_key=api_key,
        http_options={"timeout": 180000},
    )

    metrics_json = json.dumps(
        business_metrics,
        indent=4,
    )

    instructions = """

    Structure the report into these sections:
    1. Executive Summary
    2. Financial Performance
    3. Inventory and Waste Analysis
    4. Areas of Concern
    5. Recommended Management Actions
    6. Monthly Trend Analysis
    7. Product and Category Performance
    8. Regional Trend Analysis
    9. Statistical Anomaly Detection

    ANALYSIS RULES:
    - Use only supplied figures and analytical results. Never invent data, recalculate or alter supplied results, or assume unproven causes.
    - Analyse monthly revenue and gross-profit changes using complete-month comparisons. If the monthly trend status is "insufficient", state that there are not enough complete months for a month-over-month assessment.
    - Distinguish isolated declines from sustained deterioration. Only identify sustained trends when supported by the supplied consecutive-decline results.
    - Analyse product and category declines for the supplied comparison month, reporting actual revenue, percentage change, and revenue lost for every supplied result.
    - Analyse regional revenue and gross-profit declines for the supplied comparison month, reporting percentage changes and actual monetary losses.
    - If a decline list is empty, do not invent examples or substitute older declines.
    - Prioritise management attention according to supplied monetary and percentage changes without asserting unproven causes.

    ANOMALY DETECTION RULES:
    - Analyse daily IQR results separately for revenue, gross profit, and waste cost.
    - Respect each metric's supplied status. For "insufficient_data", state that daily observations were insufficient; do not claim that no anomalies were detected. If the metric was analysed and its anomaly count is zero, explicitly state that no anomalies were detected.
    - Report the supplied lower and upper IQR thresholds. For every metric with anomalies, list every supplied anomalous date, financial figure, and classification as unusually high or low. Never omit records or replace the complete list with a selection or range.
    - Treat outliers as statistical observations, not proof of fraud, operational failure, or confirmed business problems. Do not infer causes; recommendations may suggest investigating unusual observations without presenting possible explanations as facts.

    INVENTORY AND WASTE ANALYSIS:
    - Report total waste units, total units handled, waste rate, total waste cost, and waste cost as a percentage of revenue.
    - Identify products and categories with the highest waste costs, compare waste costs across regions, and analyse monthly waste trends, highlighting significant increases or decreases.
    - Distinguish high absolute waste costs from high waste rates. High waste costs alone do not establish inefficiency.
    - Do not invent or assume causes of inventory waste.

    FINANCIAL AND FORMATTING RULES:
    - The dataset does not specify a currency. Use "currency units" without currency symbols or currency names.
    - Use standard Markdown, clear and consistent section headings, and readable, consistently formatted figures with commas for thousands and two decimal places where appropriate.
    - Use level-two Markdown headings (##) for main sections, approximately twice the visual size of body text. Use level-three headings (###) for subsections only when necessary.
    - Write concise, properly spaced sentences. Break up long paragraphs and use bullet points when presenting multiple products, categories, regions, monthly changes, anomalies, or individual results.
    - Keep sections focused and avoid repeating detailed findings across sections; summarise previously reported information when necessary without omitting required analysis.
    - Bold important figures, percentages, monetary losses, anomaly counts, and key findings where useful.
    - Present management recommendations as bullet points.
    - Do not use tables, HTML, or code formatting.   
    """

    prompt = f"""
    BUSINESS PERFORMANCE DATA:

    {metrics_json}

    Prepare the management report using the supplied data and instructions.
    """

    print("Sending request to Gemini...")

    for attempt in range(3):
        try:
            response = client.interactions.create(
                model="gemini-3.5-flash-lite",
                input=prompt,
                system_instruction=instructions,
            )
            return response.output_text

        except Exception as error:
            error_message = str(error).lower()

            temporary_errors = [
                "503",
                "server disconnected",
                "connection",
                "timeout",
            ]

            is_temporary = any(
                message in error_message
                for message in temporary_errors
            )

            if is_temporary and attempt < 2:
                time.sleep(10 * (attempt + 1))
            else:
                raise
    