import psycopg2
from psycopg2 import sql

# Change these according to your local setup
DB_NAME = "postgres"
DB_USER = "carterrobinson"     # <— YOUR macOS username!
DB_PASSWORD = ""                   # probably no password
DB_HOST = "localhost"
DB_PORT = "5432"

def execute_sql_file(cursor, filename):
    with open(filename, 'r') as f:
        sql_content = f.read()
    cursor.execute(sql_content)

def main():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database successfully!")

        # Create schema
        print("📜 Creating tables...")
        execute_sql_file(cursor, 'database/schema.sql')
        
        # Insert dummy data
        print("📦 Inserting dummy data...")
        execute_sql_file(cursor, 'database/dummy_data.sql')

        cursor.close()
        conn.close()
        print("🎉 Database initialized successfully!")

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")

if __name__ == "__main__":
    main()
