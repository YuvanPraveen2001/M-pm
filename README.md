# Text-to-SQL Web Application

This is a Python-based web application that allows you to query your SQL database using natural language. You provide your database credentials and ask a question like "show me all employees in the engineering department", and the application will generate the appropriate SQL query, execute it, and display the results.

## Features

-   **Natural Language to SQL**: Converts plain English questions into SQL queries.
-   **Web-Based Interface**: Simple and intuitive HTML interface for interaction.
-   **Database Agnostic**: Uses SQLAlchemy to connect to a wide range of SQL databases (PostgreSQL, MySQL, SQLite, etc.).
-   **Schema-Aware**: Automatically inspects the database schema to generate accurate queries.
-   **Sample Database**: Includes a setup script to create a sample SQLite database for quick testing.

## Project Structure

```
.
├── app/
│   └── app.py              # Main Flask application logic
├── templates/
│   ├── index.html          # The main page with the query form
│   └── result.html         # The page to display the results
├── .env.example            # Example environment file for API keys
├── requirements.txt        # Python dependencies
├── setup_database.py       # Script to create the sample database
└── README.md
```

## Setup and Installation

### Prerequisites

-   Python 3.7+
-   An OpenAI API key

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
```

Then, install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

The application requires an OpenAI API key to function.

1.  Make a copy of the example environment file:
    ```bash
    cp .env.example .env
    ```
2.  Open the `.env` file and add your OpenAI API key:
    ```
    OPENAI_API_KEY="your_openai_api_key_here"
    ```

## Usage

### 1. Create the Sample Database (Optional)

If you want to test the application with a sample database, run the setup script:

```bash
python setup_database.py
```
This will create a `sample.db` file in the root directory.

### 2. Run the Application

Start the Flask web server:

```bash
python app/app.py
```

The application will be running at `http://127.0.0.1:5001`.

### 3. Use the Web Interface

1.  Open your web browser and navigate to `http://127.0.0.1:5001`.
2.  In the "Database Connection URI" field, enter the connection string for your database. For the sample database, the default value `sqlite:///sample.db` is already provided.
3.  In the "Your Question" field, type a question in natural language (e.g., "How many male employees are there?").
4.  Click "Ask". The application will display the generated SQL query and the results from your database.

## Technologies Used

-   **Backend**: Flask
-   **Database ORM**: SQLAlchemy
-   **NL-to-SQL**: LangChain, OpenAI (GPT-3.5-turbo)
-   **Frontend**: HTML, CSS
