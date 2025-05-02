# backend/app.py

import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import mysql.connector
from decimal import Decimal
from datetime import datetime, date
from backend.text2sql_model import convert_to_sql  # This uses the API key

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "560066",
    "database": "ava_datahub"
}

@app.get("/", response_class=HTMLResponse)
def form_view(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
def run_query(request: Request, nl_query: str = Form(""), query: str = Form("")):
    try:
        if not query and nl_query:
            query = convert_to_sql(nl_query)
            print("Generated SQL:", query)

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        columns = cursor.column_names
        cursor.close()
        conn.close()

        def convert(value):
            if isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                return value.strftime('%Y-%m-%d')
            return value

        data = [{col: convert(val) for col, val in zip(columns, row)} for row in result]

        return templates.TemplateResponse("index.html", {
            "request": request,
            "nl_query": nl_query,
            "query": query,
            "columns": columns,
            "rows": result,
            "chart_data": data
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "nl_query": nl_query,
            "query": query,
            "error": str(e)
        })
