import os
import requests
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from datetime import datetime

# It's a good practice to use a .env file for configuration
from dotenv import load_dotenv
load_dotenv()

# API Endpoint
CHAT_API_URL = "http://35.193.206.38:8000/chat"

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    db_uri = request.form.get('db_uri')
    natural_language_query = request.form.get('query')
    # The schema_text is no longer used for local processing,
    # but we'll pass it to the new API as part of the system prompt.
    schema_text = request.form.get('schema_text')
    sql_query = ""

    if not db_uri or not natural_language_query:
        return render_template('result.html', error="Database URI and query are required.")

    try:
        # Construct the payload for the external API
        # The user's curl example had a placeholder for the schema, so we'll use schema_text
        # It also had metadata for date and siteId, we can replicate that structure.
        current_date = datetime.now().strftime('%Y-%m-%d')
        payload = {
            "conversation": [
                {
                    "role": "system",
                    "content": schema_text if schema_text else "No schema provided."
                },
                {
                    "role": "system",
                    "content": f"metadata: {{currentDate: {current_date}, siteId: 2}}"
                },
                {
                    "role": "user",
                    "content": natural_language_query
                }
            ]
        }

        print(f"Sending request to API: {CHAT_API_URL}")
        response = requests.post(CHAT_API_URL, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        response_data = response.json()

        # The API response has a 'response' key with the SQL string
        sql_query = response_data.get("response")

        if not sql_query:
            return render_template('result.html',
                                   query=natural_language_query,
                                   sql_query="No SQL query returned from API.",
                                   error="The API did not return a valid SQL query in the 'response' key.",
                                   results=[])

        print(f"Received SQL from API: {sql_query}")

        # Execute the query from the API
        engine = create_engine(db_uri)
        with engine.connect() as connection:
            results = connection.execute(text(sql_query)).mappings().all()

        results_as_dicts = [dict(row) for row in results]

        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query,
                               results=results_as_dicts)

    except requests.exceptions.RequestException as e:
        error_message = f"Error connecting to the chat API: {e}"
        return render_template('result.html',
                               query=natural_language_query,
                               sql_query="API connection error.",
                               error=error_message,
                               results=[])
    except OperationalError as e:
        error_message = f"Database error executing the query: {e}"
        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query,
                               error=error_message,
                               results=[])
    except Exception as e:
        error_message = str(e)
        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query if sql_query else "Error during processing.",
                               error=error_message,
                               results=[])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
