import os
import requests
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from app.schema_utils import get_schema_documents_from_text
from datetime import datetime

# It's a good practice to use a .env file for configuration
from dotenv import load_dotenv
load_dotenv()

# Constants
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "phi3:mini"
CHAT_API_URL = "http://35.193.206.38:8000/chat"


app = Flask(__name__, template_folder='../templates')

def get_vector_store_retriever(embeddings, db_uri, schema_text=None):
    """
    Creates a retriever from either a user-provided schema text or a persisted ChromaDB index.
    """
    if schema_text and schema_text.strip():
        print("Creating in-memory vector store from provided schema text.")
        schema_docs = get_schema_documents_from_text(schema_text)
        vector_store = Chroma.from_documents(
            documents=schema_docs,
            embedding=embeddings,
            collection_name="temp_collection"
        )
    else:
        print(f"Loading persisted vector store from: {CHROMA_DB_PATH}")
        if not os.path.exists(CHROMA_DB_PATH):
            raise FileNotFoundError(f"ChromaDB index not found at '{CHROMA_DB_PATH}'. Please run the indexing script first: `python index_schema.py \"{db_uri}\"`")
        vector_store = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
    return vector_store.as_retriever()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    db_uri = request.form.get('db_uri')
    # Automatically correct common SQL Server connection string issue
    if db_uri and db_uri.startswith('sqlserver://'):
        db_uri = db_uri.replace('sqlserver://', 'mssql+pyodbc://', 1)
        print(f"Corrected DB URI to: {db_uri}")

    natural_language_query = request.form.get('query')
    schema_text = request.form.get('schema_text')
    model_choice = request.form.get('model_choice', 'local') # Default to local
    sql_query = ""

    if not db_uri or not natural_language_query:
        return render_template('result.html', error="Database URI and query are required.")

    try:
        engine = create_engine(db_uri)

        if model_choice == 'external':
            # --- EXTERNAL API LOGIC ---
            print("--- Using External API ---")
            current_date = datetime.now().strftime('%Y-%m-%d')
            payload = {
                "conversation": [
                    {"role": "system", "content": schema_text if schema_text else "No schema provided."},
                    {"role": "system", "content": f"metadata: {{currentDate: {current_date}, siteId: 2}}"},
                    {"role": "user", "content": natural_language_query}
                ]
            }
            response = requests.post(CHAT_API_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            sql_query = response_data.get("response")
            if not sql_query:
                raise ValueError("The API did not return a valid SQL query in the 'response' key.")

            print(f"Received SQL from API: {sql_query}")
            with engine.connect() as connection:
                results = connection.execute(text(sql_query)).mappings().all()
            results_as_dicts = [dict(row) for row in results]
            return render_template('result.html', query=natural_language_query, sql_query=sql_query, results=results_as_dicts)

        else:
            # --- LOCAL MODEL LOGIC ---
            print("--- Using Local Model ---")
            embeddings = OllamaEmbeddings(model=EMBED_MODEL)
            retriever = get_vector_store_retriever(embeddings, db_uri, schema_text)
            llm = ChatOllama(model=CHAT_MODEL)
            last_error = ""

            for attempt in range(3):
                print(f"--- Attempt {attempt + 1} ---")
                error_feedback = f"The previous query I tried was:\n```sql\n{sql_query}\n```\nIt failed with the following error:\n`{last_error}`\nPlease correct the query based on this error." if last_error else ""

                template = f"""You are an expert T-SQL developer. Based on the table schema below, write a SQL query for Microsoft SQL Server that would answer the user's question.
Your response should only be the SQL query, without any explanation or markdown.

Schema:
{{context}}

{error_feedback}

Question: {{question}}

SQL Query:"""
                prompt = ChatPromptTemplate.from_template(template)
                rag_chain = ({"context": retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
                sql_query = rag_chain.invoke(natural_language_query)
                print(f"Generated SQL: {sql_query}")

                if "```sql" in sql_query:
                    sql_query = sql_query.split("```sql")[1].split("```")[0].strip()

                try:
                    with engine.connect() as connection:
                        results = connection.execute(text(sql_query)).mappings().all()
                    results_as_dicts = [dict(row) for row in results]
                    return render_template('result.html', query=natural_language_query, sql_query=sql_query, results=results_as_dicts)
                except OperationalError as e:
                    last_error = str(e)
                    print(f"Query failed with error: {last_error}")

            # If all retries fail
            return render_template('result.html', query=natural_language_query, sql_query=sql_query, error=f"The query failed after multiple attempts. Last error: {last_error}")

    except Exception as e:
        error_message = str(e)
        if "Connection refused" in str(e):
            error_message = "Could not connect to Ollama or the External API. Please make sure the selected service is running."
        return render_template('result.html', query=natural_language_query, sql_query=sql_query if sql_query else "Error during processing.", error=error_message, results=[])

if __name__ == '__main__':
    app.run(debug=True, port=5001)
