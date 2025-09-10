import os
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# It's a good practice to use a .env file for configuration
from dotenv import load_dotenv
load_dotenv()

# Constants
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "phi3:mini"

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

    if not os.path.exists(CHROMA_DB_PATH):
        return render_template('result.html',
                               query=natural_language_query,
                               error=f"ChromaDB index not found at '{CHROMA_DB_PATH}'. Please run the indexing script first: `python index_schema.py \"{db_uri}\"`")

    sql_query = ""
    try:
        embeddings = OllamaEmbeddings(model=EMBED_MODEL)
        vector_store = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        retriever = vector_store.as_retriever()
        llm = ChatOllama(model=CHAT_MODEL)

        template = """
        Based on the table schema below, write a SQL query that would answer the user's question.
        Pay attention to the user's question to determine the necessary tables and columns.
        Your response should only be the SQL query, without any explanation or markdown.

        Schema:
        {context}

        Question: {question}

        SQL Query:
        """
        prompt = ChatPromptTemplate.from_template(template)

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        print("Generating SQL query...")
        sql_query = rag_chain.invoke(natural_language_query)
        print(f"Generated SQL: {sql_query}")

        # Clean up the generated query from markdown, if present
        if "```sql" in sql_query:
            sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
        elif "```" in sql_query:
            sql_query = sql_query.split("```")[1].split("```")[0].strip()

        engine = create_engine(db_uri)
        with engine.connect() as connection:
            results = connection.execute(text(sql_query)).mappings().all()

        results_as_dicts = [dict(row) for row in results]

        return render_template('result.html',
                               query=natural_language_query,
                               sql_query=sql_query,
                               results=results_as_dicts)

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
