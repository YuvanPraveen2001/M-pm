import os
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from schema_utils import get_schema_documents_from_text

# It's a good practice to use a .env file for configuration
from dotenv import load_dotenv
load_dotenv()

# Constants
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "phi3:mini"

app = Flask(__name__, template_folder='../templates')

def get_vector_store_retriever(embeddings, db_uri, schema_text=None):
    """
    Creates a retriever from either a user-provided schema text or a persisted ChromaDB index.
    """
    if schema_text and schema_text.strip():
        print("Creating in-memory vector store from provided schema text.")
        # Create documents from the schema text using the utility function
        schema_docs = get_schema_documents_from_text(schema_text)
        # Create an in-memory vector store
        vector_store = Chroma.from_documents(
            documents=schema_docs,
            embedding=embeddings,
            collection_name="temp_collection"  # Use a temporary collection name
        )
    else:
        print(f"Loading persisted vector store from: {CHROMA_DB_PATH}")
        # Check if the persisted ChromaDB directory exists
        if not os.path.exists(CHROMA_DB_PATH):
            raise FileNotFoundError(f"ChromaDB index not found at '{CHROMA_DB_PATH}'. Please run the indexing script first: `python index_schema.py \"{db_uri}\"`")
        # Load the persisted vector store
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
    natural_language_query = request.form.get('query')
    schema_text = request.form.get('schema_text')

    if not db_uri or not natural_language_query:
        return render_template('result.html', error="Database URI and query are required.")

    try:
        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        retriever = get_vector_store_retriever(embeddings, db_uri, schema_text)
        llm = ChatOllama(model=CHAT_MODEL)
        engine = create_engine(db_uri)

        sql_query = ""
        last_error = ""

        for attempt in range(3):
            print(f"--- Attempt {attempt + 1} ---")

            error_feedback = ""
            if last_error:
                error_feedback = f"""
The previous query I tried was:
```sql
{sql_query}
```
It failed with the following error:
`{last_error}`

Please correct the query based on this error.
"""

            template = f"""
            Based on the table schema below, write a SQL query that would answer the user's question.
            Pay attention to the user's question to determine the necessary tables and columns.
            Your response should only be the SQL query, without any explanation or markdown.

            Schema:
            {{context}}

            {error_feedback}

            Question: {{question}}

            SQL Query:
            """
            prompt = ChatPromptTemplate.from_template(template)

            rag_chain = (
                { "context": retriever, "question": RunnablePassthrough() }
                | prompt
                | llm
                | StrOutputParser()
            )

            print("Generating SQL query...")
            sql_query = rag_chain.invoke(natural_language_query)
            print(f"Generated SQL: {sql_query}")

            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].split("```")[0].strip()

            try:
                with engine.connect() as connection:
                    results = connection.execute(text(sql_query)).mappings().all()

                results_as_dicts = [dict(row) for row in results]

                return render_template('result.html',
                                       query=natural_language_query,
                                       sql_query=sql_query,
                                       results=results_as_dicts)
            except OperationalError as e:
                last_error = str(e)
                print(f"Query failed with error: {last_error}")
                # Loop will continue for the next attempt
            except Exception as e:
                # For non-database errors, we probably want to stop.
                raise e

        # If all retries fail
        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query,
                               error=f"The query failed after multiple attempts. Last error: {last_error}")

    except Exception as e:
        error_message = str(e)
        if "Connection refused" in error_message:
            error_message = "Could not connect to Ollama. Please make sure Ollama is running and the specified models are available."

        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query if sql_query else "Error generating SQL.",
                               error=error_message)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
