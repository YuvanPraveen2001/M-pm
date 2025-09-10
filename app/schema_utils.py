import re
from sqlalchemy import create_engine, inspect
from langchain.docstore.document import Document

def get_schema_documents_from_uri(db_uri: str):
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

def get_schema_documents_from_text(schema_text: str):
    """
    Parses a schema provided in a specific text format and converts it
    into a list of Document objects.
    """
    documents = []

    # Regex to find all matches
    table_pattern = re.compile(r"\[table: (.*?)\]")
    column_pattern = re.compile(r"\[table: (.*?)\] \[col: (.*?)\] \[type: (.*?)\]")

    # Find all table definitions first
    table_matches = table_pattern.findall(schema_text)
    column_matches = column_pattern.findall(schema_text)

    # Keep track of tables found in column definitions to avoid duplicating table docs
    tables_from_columns = {col[0] for col in column_matches}

    all_table_names = set(table_matches) | tables_from_columns

    for table_name in all_table_names:
        table_doc_content = f"[table: {table_name}]"
        documents.append(Document(page_content=table_doc_content, metadata={"type": "table", "table_name": table_name}))

    for table_name, col_name, col_type in column_matches:
        col_doc_content = f"[table: {table_name}] [col: {col_name}] [type: {col_type}]"
        documents.append(Document(page_content=col_doc_content, metadata={"type": "column", "table_name": table_name, "column_name": col_name}))

    print(f"Parsed {len(documents)} schema elements from text.")
    return documents
