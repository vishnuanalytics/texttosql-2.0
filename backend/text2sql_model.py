import os
import re
import csv
import requests
from datetime import datetime
from dotenv import load_dotenv

# Always load the .env file from the same folder as this script
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError("OPENROUTER_API_KEY is not set in the .env file")

# Path to the log CSV
LOG_FILE = os.path.join(os.path.dirname(__file__), "query_logs.csv")

# Ensure header row exists
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "nl_query", "sql_query", "status_code", "response"])

def extract_sql(text: str) -> str:
    code_blocks = re.findall(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL)
    return code_blocks[0].strip() if code_blocks else text.strip()

def log_query(nl_query, sql_query, status_code, response_text):
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().isoformat(),
            nl_query,
            sql_query,
            status_code,
            response_text[:300].replace("\n", " ")
        ])

def convert_to_sql(nl_query: str) -> str:
    schema_description = """
        You are an expert MySQL assistant. The database has the following tables and columns:

        Table: common_biz
        - biz_id (INT): Unique identifier for each business
        - biz_name (VARCHAR): Name of the business
        - country (VARCHAR): Country where the business operates

        Table: common_bizlocation
        - biz_location_id (INT): Unique ID for each business location
        - biz_location_nick_name (VARCHAR): location name
        - biz_id (INT): Foreign key to common_biz
        - city (VARCHAR): City of the location

        Table: common_order
        - order_id (INT): Unique order ID
        - biz_id (INT): Foreign key to common_biz
        - biz_location_id (INT): Foreign key to common_bizlocation
        - order_subtotal (DECIMAL): Subtotal of the order
        - order_total (DECIMAL): Total order amount
        - fulfillment_mode (VARCHAR): e.g., delivery, pickup
        - created (DATETIME): Order date and time
        - order_channel (VARCHAR): Channel/aggregator like Swiggy, Zomato

        Respond with a valid SQL query in a code block, without explanations. Only use these tables and columns."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://127.0.0.1:8000",  # Replace with your domain
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": schema_description},
            {"role": "user", "content": nl_query}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        full_text = response.json()["choices"][0]["message"]["content"]
        sql_query = extract_sql(full_text)
        log_query(nl_query, sql_query, response.status_code, full_text)
        return sql_query
    else:
        error_text = response.text
        log_query(nl_query, "", response.status_code, error_text)
        raise Exception(f"OpenRouter Error: {response.status_code} - {error_text}")
