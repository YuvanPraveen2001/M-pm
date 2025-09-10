import os
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain.chains import create_sql_query_chain

# It's a good practice to use environment variables for sensitive data like API keys
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    db_uri = request.form.get('db_uri')
    natural_language_query = request.form.get('query')

    if not db_uri or not natural_language_query:
        return render_template('result.html', error="Database URI and query are required.")

    # Check for API key before proceeding
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here" or api_key == "dummy_key":
         return render_template('result.html',
                               query=natural_language_query,
                               sql_query="Not attempted.",
                               error="OPENAI_API_KEY is not set or is a placeholder. Please set a valid key in the .env file.")

    sql_query = ""
    try:
        # Lazy load the LLM and chain inside the request
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
        db = SQLDatabase.from_uri(db_uri)

        chain = create_sql_query_chain(llm, db)
        sql_query = chain.invoke({"question": natural_language_query})

        # Clean up the generated query from markdown
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()

        engine = create_engine(db_uri)
        with engine.connect() as connection:
            results = connection.execute(text(sql_query)).mappings().all()

        results_as_dicts = [dict(row) for row in results]

        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query,
                               results=results_as_dicts)

    except Exception as e:
        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query if sql_query else "Error generating SQL.",
                               error=str(e))

if __name__ == '__main__':
    # The check for OPENAI_API_KEY is now inside the /query route.
    app.run(debug=True, port=5001)
