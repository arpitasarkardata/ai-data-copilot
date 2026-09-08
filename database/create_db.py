import pandas as pd
import sqlite3
import os

# Paths
CSV_PATH = os.path.join("..", "data", "Loan_Default.csv")
DB_PATH = os.path.join("..", "database", "analytics.db")

def create_database():
    # Load the CSV
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    print("Columns:", list(df.columns))

    # Connect to SQLite (creates the file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)

    # Write dataframe to a table called 'loans'
    df.to_sql("loans", conn, if_exists="replace", index=False)

    conn.close()
    print(f"Database created at {DB_PATH}")

if __name__ == "__main__":
    create_database()