import argparse
from sqlalchemy import create_engine, inspect
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain.docstore.document import Document

# Constants
DB_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
EMBED_MODEL = "nomic-embed-text"

def get_schema_documents(db_uri: str):
    """
    Connects to a SQL database and extracts its schema, formatting it
    into a list of Document objects for embedding.
    """
    print(f"Connecting to the database at {db_uri} to extract schema...")
    engine = create_engine(db_uri)
    inspector = inspect(engine)

    documents = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)

        table_doc_content = f"[table: {table_name}]"
        documents.append(Document(page_content=table_doc_content, metadata={"type": "table", "table_name": table_name}))

        for column in columns:
            col_name = column['name']
            col_type = str(column['type'])

            col_doc_content = f"[table: {table_name}] [col: {col_name}] [type: {col_type}]"
            documents.append(Document(page_content=col_doc_content, metadata={"type": "column", "table_name": table_name, "column_name": col_name}))

    print(f"Found {len(documents)} schema elements (tables and columns).")
    return documents

def main():
    parser = argparse.ArgumentParser(description="Index a SQL database schema into ChromaDB.")
    parser.add_argument("db_uri", type=str, help="The connection URI for the SQL database (e.g., 'sqlite:///sample.db').")
    args = parser.parse_args()

    print("Starting schema indexing process...")

    schema_documents = get_schema_documents(args.db_uri)

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
