import os
import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURATION ---
# Replace these with your Render Postgres credentials
PG_USER = "user1"
PG_PASSWORD = "BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ"
PG_HOST = "dpg-d3g661u3jp1c73eg9v1g-a.render.com"      # something like xyz.render.com
PG_PORT = "5432"               # default Postgres port
PG_DB = "crime_rate_h3u5"

# Folder containing your CSVs
CSV_FOLDER = "./data"  # e.g., "./csvs"

# --- CREATE CONNECTION ---
engine = create_engine(
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

# --- UPLOAD CSVs ---
# Loop through all CSV files in the folder
for filename in os.listdir(CSV_FOLDER):
    if filename.endswith(".csv"):
        file_path = os.path.join(CSV_FOLDER, filename)
        table_name = os.path.splitext(filename)[0]  # use filename as table name

        # Read CSV
        df = pd.read_csv(file_path)

        # Upload to Postgres
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"Uploaded {filename} to table {table_name}")

print("All CSVs uploaded successfully!")
