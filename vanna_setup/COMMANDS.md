# Vanna.AI Commands

## Quick Setup Commands

### 1. Navigate to the folder
```bash
cd vanna_setup
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment file
```bash
# Copy the example file
cp env_example.txt .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 4. Make sure MySQL is running
```bash
# Check if running
docker ps

# If not running, start it
docker start rethinkai-mysql
```

### 5. Run Vanna.AI
```bash
python vanna_mysql.py
```

## What Happens When You Run It

1. **Setup**: Initializes Vanna.AI with OpenAI and ChromaDB
2. **Connect**: Connects to your local MySQL database
3. **Train**: Trains on your database schema (one-time process)
4. **Custom Training**: Adds specific training data about your 911 data
5. **Interactive Mode**: Allows you to ask questions

## Example Session

```
🚨 Vanna.AI Setup for Boston 911 Data
==================================================
🚀 Setting up Vanna.AI...
✅ Vanna.AI initialized with OpenAI and ChromaDB
🔗 Connecting to local MySQL database...
✅ Connected to MySQL database
🎓 Training Vanna.AI on your database...
📊 Getting database schema...
✅ Found 45 columns
📋 Creating training plan...
📝 Training plan created with 12 items
🚀 Training model...
✅ Training completed!
📚 Adding custom training data...
✅ Custom training data added!

🎉 Setup complete! You can now ask questions about your data.

💬 Interactive mode (type 'quit' to exit):

❓ Ask a question: How many shooting incidents were there in 2023?
🔍 Generated SQL: SELECT COUNT(*) as total_shots FROM shots_fired_data WHERE YEAR(incident_date_time) = 2023
📊 Result: [{'total_shots': 1234}]
```

## Troubleshooting Commands

### If MySQL connection fails:
```bash
# Check if container is running
docker ps

# Check container logs
docker logs rethinkai-mysql

# Restart container if needed
docker restart rethinkai-mysql
```

### If OpenAI API fails:
```bash
# Check your API key
echo $OPENAI_API_KEY

# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models
```

### If training fails:
```bash
# Check if you have data
python -c "
import mysql.connector
conn = mysql.connector.connect(host='localhost', user='rethinkai_user', password='MySecureUserPass123!', database='rethinkai_db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM shots_fired_data')
print('Shots fired records:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM homicide_data')
print('Homicide records:', cursor.fetchone()[0])
conn.close()
"
```

## Advanced Commands

### Run without interactive mode:
```bash
python -c "
from vanna_mysql import setup_vanna, connect_to_database, ask_question
vn = setup_vanna()
connect_to_database(vn)
ask_question(vn, 'How many shootings were there?')
"
```

### Clear training data and retrain:
```bash
# Delete ChromaDB data
rm -rf ./chroma_db

# Run again to retrain
python vanna_mysql.py
```

## Expected Results

After running successfully, you should be able to ask questions like:
- "How many shooting incidents were there in 2023?"
- "Which district has the most shootings?"
- "Show me shootings with ballistics evidence"
- "What are the trends in shooting incidents over time?"
