import os
import pandas as pd
from sqlalchemy import create_engine, text
import glob

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

LOCAL_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def upload_csvs():
    csv_paths = sorted(glob.glob(os.path.join(LOCAL_DATA_DIR, "*.csv")))
    if not csv_paths:
        print(f"No CSV files found in {LOCAL_DATA_DIR}")
        return

    for file_path in csv_paths:
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        print(f"Uploading {table_name} from {file_path}...")
        df = pd.read_csv(file_path)
        df.to_sql(table_name, engine, if_exists="replace", index=False)

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
