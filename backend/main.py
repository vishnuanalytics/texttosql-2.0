from fastapi import FastAPI, Request
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

# Database config
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "560066",
    "database": "ava_datahub"
}

class SQLRequest(BaseModel):
    query: str

@app.get("/")
async def root():
    return {"message": "Welcome to the SQL API!"}

@app.post("/run-sql")
async def run_sql(request: SQLRequest):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute(request.query)

        # Fetch results if it's a SELECT query
        if request.query.strip().lower().startswith("select"):
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            data = [dict(zip(columns, row)) for row in result]
        else:
            connection.commit()
            data = {"message": "Query executed successfully."}

        cursor.close()
        connection.close()
        return {"success": True, "data": data}

    except Exception as e:
        return {"success": False, "error": str(e)}
