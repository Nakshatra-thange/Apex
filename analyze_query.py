import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from the backend's .env file
load_dotenv(dotenv_path='./backend/.env')

# Get the database URL and adjust it for the psycopg2 driver
db_url = os.getenv("DATABASE_URL").replace("postgresql+asyncpg", "postgresql")

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()

    # --- PASTE THE QUERY YOU WANT TO ANALYZE HERE ---
    query_to_analyze = "SELECT * FROM users WHERE email = 'test@example.com';"
    # --------------------------------------------------

    print(f"🔬 Analyzing query: {query_to_analyze}\n")
    
    # Prefix the query with EXPLAIN ANALYZE
    cursor.execute(f"EXPLAIN ANALYZE {query_to_analyze}")
    
    query_plan = cursor.fetchall()

    print("--- QUERY EXECUTION PLAN ---")
    for row in query_plan:
        print(row[0])
    
    cursor.close()

except Exception as e:
    print(f"❌ An error occurred: {e}")

finally:
    if 'conn' in locals() and conn is not None:
        conn.close()
        print("\nConnection closed.")