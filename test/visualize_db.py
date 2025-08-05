import sqlite3
import pandas as pd
from tabulate import tabulate

def visualize_db(db_path):
    """
    Simple SQLite database visualizer that shows all tables and their contents
    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Get list of tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print(f"\nDatabase: {db_path}")
        print("-" * 50)
        
        # Display each table
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            print("-" * len(f"Table: {table_name}"))
            
            # Get table data
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Display table info
            print(f"Columns: {', '.join(df.columns)}")
            print(f"Total rows: {len(df)}")
            
            # Display first 5 rows in a nice table format
            if not df.empty:
                print("\nFirst 5 rows:")
                print(tabulate(df.head(), headers='keys', tablefmt='psql', showindex=False))
            else:
                print("(Empty table)")
            
            print("\n" + "=" * 50)
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Example usage - replace with your actual database path
    db_path = r"C:\Dev\PyTracker\storage\User_db"
    visualize_db(db_path)