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
    Parses a schema provided as SQL CREATE TABLE statements and converts it
    into a list of Document objects.
    """
    documents = []
    # Regex to find all CREATE TABLE statements
    create_table_pattern = re.compile(r"CREATE TABLE (.*?)\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)

    # Regex to find column definitions within a CREATE TABLE statement
    column_pattern = re.compile(r"^\s*(\w+)\s+([\w\(\)]+)", re.MULTILINE)

    table_matches = create_table_pattern.findall(schema_text)

    for table_match in table_matches:
        full_table_name = table_match[0].strip()
        # In case the table name is quoted or has schema info, we take the last part
        simple_table_name = full_table_name.split('.')[-1].strip('[]"')

        table_doc_content = f"[table: {simple_table_name}]"
        documents.append(Document(page_content=table_doc_content, metadata={"type": "table", "table_name": simple_table_name}))

        columns_text = table_match[1]
        column_matches = column_pattern.findall(columns_text)

        for col_match in column_matches:
            col_name = col_match[0].strip()
            col_type = col_match[1].strip()

            if col_name.upper() in ["CONSTRAINT", "PRIMARY", "FOREIGN", "DEFAULT", "CHECK"]:
                continue

            col_doc_content = f"[table: {simple_table_name}] [col: {col_name}] [type: {col_type}]"
            documents.append(Document(page_content=col_doc_content, metadata={"type": "column", "table_name": simple_table_name, "column_name": col_name}))

    print(f"Parsed {len(documents)} schema elements from the provided SQL DDL text.")
    return documents
