import argparse
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from app.schema_utils import get_schema_documents_from_uri

# Constants
DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"

def main():
    parser = argparse.ArgumentParser(description="Index a SQL database schema into ChromaDB.")
    parser.add_argument("db_uri", type=str, help="The connection URI for the SQL database (e.g., 'sqlite:///sample.db').")
    args = parser.parse_args()

    db_uri = args.db_uri
    # Automatically correct common SQL Server connection string issue
    if db_uri and db_uri.startswith('sqlserver://'):
        db_uri = db_uri.replace('sqlserver://', 'mssql+pyodbc://', 1)
        print(f"Corrected DB URI to: {db_uri}")

    print("Starting schema indexing process...")

    schema_documents = get_schema_documents_from_uri(db_uri)

    if not schema_documents:
        print("No schema information found or database is empty. Exiting.")
        return

    print(f"Initializing embedding model via Ollama: {EMBED_MODEL}")
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)

    print(f"Creating ChromaDB vector store at: {DB_PATH}")
    print(f"Using collection: {COLLECTION_NAME}")

    vector_store = Chroma.from_documents(
        documents=schema_documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=DB_PATH
    )

    print("\nSchema indexing complete!")
    print(f"The schema has been successfully embedded and stored in ChromaDB at '{DB_PATH}'.")

if __name__ == "__main__":
    main()
