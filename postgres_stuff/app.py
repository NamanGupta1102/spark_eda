import os
import pandas as pd
from sqlalchemy import create_engine, text
import requests
import io

# --- ENV VARS (Render will handle these) ---
PG_USER = "user1"
PG_PASSWORD = "BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ"
PG_HOST = "dpg-d3g661u3jp1c73eg9v1g-a.internal"      # something like xyz.render.com
PG_PORT = "5432"               # default Postgres port
PG_DB = "crime_rate_h3u5"

# Folder containing your CSV files
CSV_FOLDER = "./data"

# --- CREATE CONNECTION ---
engine = create_engine(
    f"postgresql://user1:BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ@dpg-d3g661u3jp1c73eg9v1g-a.ohio-postgres.render.com/crime_rate_h3u5"
)

CSV_LINKS = {
    "crimes311": "https://drive.google.com/uc?export=download&id=1oUwuYMgmioHLSJq2DxzVKjm0NU6uhmu3"
    # ...
}

def upload_csvs():
    for table_name, link in CSV_LINKS.items():
        print(f"Downloading {table_name}...")
        response = requests.get(link)
        response.raise_for_status()

        df = pd.read_csv("data/Dorchester_311.csv")
        print(df.head())
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        # Print first 5 rows from the uploaded table

        print(f"📋 First 5 rows of {table_name}:")
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
            rows = result.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"  Row {i}: {row}")
        print(f"✅ Uploaded {table_name}")

if __name__ == "__main__":
    upload_csvs()
    print("🎉 All CSVs uploaded successfully.")
