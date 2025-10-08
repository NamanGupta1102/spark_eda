#!/usr/bin/env python3
"""
Simple Vanna.AI setup for MySQL database
Based on: https://vanna.ai/docs/mysql-openai-standard-chromadb/
"""

from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

def setup_vanna():
    """Setup Vanna.AI with OpenAI and ChromaDB"""
    print("🚀 Setting up Vanna.AI...")
    
    # Get OpenAI API key from environment
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("❌ Please set OPENAI_API_KEY in your .env file")
        return None
    
    # Initialize Vanna with OpenAI and ChromaDB
    vn = MyVanna(config={
        'api_key': openai_api_key, 
        'model': 'gpt-4'  # or 'gpt-3.5-turbo' for cheaper option
    })
    
    print("✅ Vanna.AI initialized with OpenAI and ChromaDB")
    return vn

def connect_to_database(vn):
    """Connect to the provided PostgreSQL database URL"""
    print("🔗 Connecting to PostgreSQL database...")

    try:
        # Provided PostgreSQL URL
        database_url = (
            "postgresql://user1:BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ@"
            "dpg-d3g661u3jp1c73eg9v1g-a.ohio-postgres.render.com/crime_rate_h3u5"
        )

        parsed = urlparse(database_url)
        host = parsed.hostname or ""
        dbname = (parsed.path or "/").lstrip("/")
        user = parsed.username or ""
        password = parsed.password or ""
        port = parsed.port or 5432

        vn.connect_to_postgres(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port,
        )
        print("✅ Connected to PostgreSQL database")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False

def train_vanna(vn):
    """Train Vanna.AI on your database schema"""
    print("🎓 Training Vanna.AI on your database...")
    
    try:
        # Get information schema
        print("📊 Getting database schema...")
        df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
        print(f"✅ Found {len(df_information_schema)} columns")
        
        # Create training plan
        print("📋 Creating training plan...")
        plan = vn.get_training_plan_generic(df_information_schema)
        print(f"📝 Training plan created")
        
        # Train the model
        print("🚀 Training model...")
        vn.train(plan=plan)
        print("✅ Training completed!")
        
        return True
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False

def add_custom_training_data(vn):
    """Add custom training data for your 911 data"""
    print("📚 Adding custom training data...")
    
    try:
        # Add DDL for your tables
        vn.train(ddl="""
        CREATE TABLE shots_fired_data (
            id VARCHAR(255) PRIMARY KEY,
            incident_date_time DATETIME,
            ballistics_evidence INT DEFAULT 0,
            latitude DECIMAL(10,8),
            longitude DECIMAL(11,8),
            district VARCHAR(10),
            neighborhood VARCHAR(100),
            year INT,
            offense_code_group VARCHAR(255),
            street VARCHAR(255)
        )
        """)
        
        vn.train(ddl="""
        CREATE TABLE homicide_data (
            id VARCHAR(255) PRIMARY KEY,
            homicide_date DATETIME,
            district VARCHAR(10),
            neighborhood VARCHAR(100),
            offense_code_group VARCHAR(255),
            street VARCHAR(255)
        )
        """)
        
        # Add business documentation
        vn.train(documentation="""
        This database contains Boston 911 crime data including:
        - shots_fired_data: Records of shooting incidents with location and timing
        - homicide_data: Records of homicide incidents
        - ballistics_evidence: 1 if confirmed, 0 if unconfirmed
        - district: Boston police district (B2, B3, C11 are Dorchester areas)
        """)
        
        # Add some example queries
        vn.train(sql="SELECT COUNT(*) as total_shots FROM shots_fired_data")
        vn.train(sql="SELECT district, COUNT(*) as shots_count FROM shots_fired_data GROUP BY district")
        vn.train(sql="SELECT YEAR(incident_date_time) as year, COUNT(*) as shots_count FROM shots_fired_data GROUP BY year ORDER BY year")
        
        print("✅ Custom training data added!")
        return True
    except Exception as e:
        print(f"❌ Failed to add custom training data: {e}")
        return False

def ask_question(vn, question):
    """Ask a question to Vanna.AI"""
    print(f"❓ Question: {question}")
    
    try:
        # Generate SQL
        sql = vn.generate_sql(question)
        print(f"🔍 Generated SQL: {sql}")
        
        # Run the query
        result = vn.run_sql(sql)
        print(f"📊 Result: {result}")
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function to setup and test Vanna.AI"""
    print("🚨 Vanna.AI Setup for Boston 911 Data")
    print("=" * 50)
    
    # Setup Vanna
    vn = setup_vanna()
    if not vn:
        return
    
    # Connect to database
    if not connect_to_database(vn):
        return
    
    # Train the model
    if not train_vanna(vn):
        return
    
    # Add custom training data
    add_custom_training_data(vn)
    
    print("\n🎉 Setup complete! You can now ask questions about your data.")
    print("\nExample questions you can ask:")
    print("- 'How many shooting incidents were there in 2023?'")
    print("- 'Which district has the most shootings?'")
    print("- 'Show me shootings with ballistics evidence'")
    print("- 'What are the trends in shooting incidents over time?'")
    
    # Interactive mode
    print("\n💬 Interactive mode (type 'quit' to exit):")
    while True:
        question = input("\n❓ Ask a question: ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        if question:
            ask_question(vn, question)

if __name__ == "__main__":
    main()
