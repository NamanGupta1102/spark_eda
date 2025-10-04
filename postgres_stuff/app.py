import os
import pandas as pd
from sqlalchemy import create_engine
import requests
import io

# --- ENV VARS (Render will handle these) ---
PG_USER = "user1"
PG_PASSWORD = "BbWTihWnsBHglVpeKK8XfQgEPDOcokZZ"
PG_HOST = "dpg-d3g661u3jp1c73eg9v1g-a.render.com"      # something like xyz.render.com
PG_PORT = "5432"               # default Postgres port
PG_DB = "crime_rate_h3u5"

# Folder containing your CSV files
CSV_FOLDER = "./data"

# --- CREATE CONNECTION ---
engine = create_engine(
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
)

CSV_LINKS = {
    "crimes311": "https://drive.google.com/file/d/1oUwuYMgmioHLSJq2DxzVKjm0NU6uhmu3/view?usp=sharing"
    # ...
}

def upload_csvs():
    for table_name, link in CSV_LINKS.items():
        print(f"Downloading {table_name}...")
        response = requests.get(link)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text))
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print(f"✅ Uploaded {table_name}")

if __name__ == "__main__":
    upload_csvs()
    print("🎉 All CSVs uploaded successfully.")
