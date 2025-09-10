# Text-to-SQL Web Application (RAG-based)

This is a Python-based web application that allows you to query your SQL database using natural language. It uses a Retrieval-Augmented Generation (RAG) architecture to provide accurate results even for complex database schemas.

The application first indexes your database schema into a vector store. Then, when you ask a question, it retrieves the most relevant parts of the schema and uses a local language model to generate the correct SQL query.

## Features

-   **RAG-based Text-to-SQL**: Uses a modern RAG architecture for high accuracy.
-   **Local LLM Support**: Powered by local models running via Ollama (e.g., `phi3:mini`).
-   **Advanced Embeddings**: Uses Nomic for high-quality schema embeddings.
-   **Vector-based Schema Search**: Stores and searches your schema efficiently using ChromaDB.
-   **Web-Based Interface**: Simple and intuitive HTML interface for interaction.
-   **Database Agnostic**: Uses SQLAlchemy to connect to a wide range of SQL databases.

## Project Structure

```
.
├── app/
│   └── app.py              # Main Flask application logic
├── templates/
│   ├── index.html          # The main page with the query form
│   └── result.html         # The page to display the results
├── .env.example            # Example environment file
├── requirements.txt        # Python dependencies
├── setup_database.py       # Script to create a sample SQL database
├── index_schema.py         # Script to index your database schema into ChromaDB
└── README.md
```

## Setup and Installation

### Prerequisites

-   Python 3.7+
-   [Ollama](https://ollama.com/) installed and running.

### 1. Clone the Repository

```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Install Dependencies

It's recommended to create a virtual environment first.

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Set Up Ollama

This application requires a running Ollama instance with the chat and embedding models pulled.

1.  Make sure your Ollama application is running.
2.  Pull the required models from the command line:
    ```bash
    ollama pull phi3:mini
    ollama pull nomic-embed-text
    ```

## Usage (Two-Step Process)

This application uses a two-step process: first you index your database schema, then you can run the web application to ask questions.

### Step 1: Index Your Database Schema

You must run the indexing script from your terminal to teach the application about your database.

-   **For the sample database:**
    ```bash
    python setup_database.py
    python index_schema.py "sqlite:///sample.db"
    ```
-   **For your own database:**
    ```bash
    python index_schema.py "your_database_connection_uri"
    ```

This will create a `./chroma_db` directory containing the vector index of your schema. You only need to run this once, or whenever your database schema changes.

### Step 2: Run the Web Application

Start the Flask web server:

```bash
python app/app.py
```

The application will be running at `http://127.0.0.1:5001`.

1.  Open your web browser and navigate to the URL.
2.  In the "Database Connection URI" field, enter the same connection string you used for indexing.
3.  In the "Your Question" field, type a question in natural language.
4.  Click "Ask". The application will display the generated SQL query and the results.

## Technologies Used

-   **Backend**: Flask
-   **Database ORM**: SQLAlchemy
-   **LLM Serving**: Ollama
-   **Chat Model**: `phi3:mini`
-   **Embedding Model**: `nomic-embed-text`
-   **Vector Database**: ChromaDB
-   **Core Framework**: LangChain
-   **Frontend**: HTML, CSS
