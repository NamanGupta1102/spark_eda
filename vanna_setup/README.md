# Vanna.AI Setup for Boston 911 Data

This folder contains a simple setup for using Vanna.AI with your local MySQL database containing Boston 911 crime data.

## What is Vanna.AI?

Vanna.AI is an AI-powered SQL generator that allows you to ask questions in natural language and get SQL queries back. It uses RAG (Retrieval Augmented Generation) with your database schema to generate accurate SQL.

## Files

- `vanna_mysql.py` - Main script for Vanna.AI setup and interaction
- `requirements.txt` - Python dependencies
- `env_example.txt` - Example environment file
- `README.md` - This documentation

## Quick Start

### Step 1: Install Dependencies
```bash
cd vanna_setup
pip install -r requirements.txt
```

### Step 2: Set Up Environment
```bash
# Copy the example environment file
cp env_example.txt .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 3: Make Sure MySQL is Running
```bash
# Check if your MySQL container is running
docker ps

# If not running, start it
docker start rethinkai-mysql
```

### Step 4: Run Vanna.AI
```bash
python vanna_mysql.py
```

## What It Does

1. **Connects** to your local MySQL database with the 911 data
2. **Trains** Vanna.AI on your database schema
3. **Adds** custom training data about your 911 data
4. **Provides** an interactive interface to ask questions

## Example Questions You Can Ask

- "How many shooting incidents were there in 2023?"
- "Which district has the most shootings?"
- "Show me shootings with ballistics evidence"
- "What are the trends in shooting incidents over time?"
- "How many homicides occurred in each district?"
- "Show me shootings in district B3"

## How It Works

1. **Training Phase**: Vanna.AI learns your database schema and structure
2. **Question Processing**: When you ask a question, it finds relevant schema information
3. **SQL Generation**: It generates appropriate SQL based on your question
4. **Query Execution**: Runs the SQL and returns results

## Database Schema

Your database contains:
- `shots_fired_data` (1,480 records) - Shooting incidents
- `homicide_data` (1 record) - Homicide incidents

## Troubleshooting

### If connection fails:
- Make sure MySQL container is running: `docker ps`
- Check your database credentials in the script

### If training fails:
- Make sure you have data in your database
- Check that the tables exist

### If OpenAI API fails:
- Verify your API key is correct
- Check you have credits in your OpenAI account

## Advanced Usage

You can also use Vanna.AI programmatically:

```python
from vanna_mysql import setup_vanna, connect_to_database, ask_question

# Setup
vn = setup_vanna()
connect_to_database(vn)

# Ask questions
result = ask_question(vn, "How many shootings were there last year?")
```

## Cost

- **Vanna.AI**: Free (uses ChromaDB locally)
- **OpenAI API**: Pay per token (very cheap for small queries)
- **MySQL**: Free (your local Docker container)

## Next Steps

Once you have this working, you can:
1. Integrate it into your Flask API
2. Create a web interface
3. Add more training data
4. Deploy to production
