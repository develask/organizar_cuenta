import os
import sqlite3
from pathlib import Path

class DatabaseConnection:
    def __init__(self):
        db_path = os.environ.get("DATABASE_PATH", "movimientos.db")
        self.db_path = Path(db_path).expanduser()
        if not self.db_path.is_absolute():
            project_root = Path(__file__).resolve().parent
            self.db_path = (project_root / self.db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = None

    def __enter__(self):
        """Enter the context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and close the connection."""
        self.close()
        return False

    def connect(self):
        """Establish a connection to the SQLite database."""
        try:
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return dictionaries instead of tuples
            self.connection.row_factory = sqlite3.Row
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def execute_query(self, query, params=None):
        """
        Execute a SQL query on the database.

        Parameters:
        query (str): The SQL query to execute.
        params (tuple, optional): Parameters to pass to the query.

        Returns:
        list: The results of the query.
        """
        if not self.connection:
            print("No database connection established.")
            return []

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")
            return []
        finally:
            cursor.close()

    def commit(self):
        """Commit the current transaction."""
        if self.connection:
            try:
                self.connection.commit()
                print("Transaction committed.")
            except sqlite3.Error as e:
                print(f"Error committing transaction: {e}")
        else:
            print("No database connection established.")

    def insert(self, table, data):
        """
        Insert data into the specified table.

        Parameters:
        table (str): The name of the table.
        data (dict): A dictionary with column names as keys and values to insert.

        Returns:
        int: The ID of the inserted row or None if failed.
        """
        if not self.connection:
            self.connect()

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, values)
            self.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
            return None
        finally:
            cursor.close()

    def select(self, table, columns="*", where=None, where_params=None):
        """
        Select data from the specified table.

        Parameters:
        table (str): The name of the table.
        columns (str): Columns to select, default is all (*).
        where (str, optional): WHERE clause.
        where_params (tuple, optional): Parameters for the WHERE clause.

        Returns:
        list: The query results.
        """
        if not self.connection:
            self.connect()

        query = f"SELECT {columns} FROM {table}"
        if where:
            query += f" WHERE {where}"

        return self.execute_query(query, where_params)

    def update(self, table, data, where, where_params):
        """
        Update data in the specified table.

        Parameters:
        table (str): The name of the table.
        data (dict): A dictionary with column names as keys and new values.
        where (str): WHERE clause.
        where_params (tuple): Parameters for the WHERE clause.

        Returns:
        int: Number of rows affected.
        """
        if not self.connection:
            self.connect()

        set_clause = ', '.join([f"{column} = ?" for column in data.keys()])
        values = tuple(data.values()) + where_params

        query = f"UPDATE {table} SET {set_clause} WHERE {where}"

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, values)
            self.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Error updating data: {e}")
            return 0
        finally:
            cursor.close()

    def delete(self, table, where, where_params):
        """
        Delete data from the specified table.

        Parameters:
        table (str): The name of the table.
        where (str): WHERE clause.
        where_params (tuple): Parameters for the WHERE clause.

        Returns:
        int: Number of rows affected.
        """
        if not self.connection:
            self.connect()

        query = f"DELETE FROM {table} WHERE {where}"

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, where_params)
            self.commit()
            return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Error deleting data: {e}")
            return 0
        finally:
            cursor.close()


with DatabaseConnection() as db:
    # ceate the table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS movimientos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        fecha_valor TEXT,
        descripcion TEXT,
        importe REAL,
        saldo REAL
    );
    """
    db.execute_query(create_table_query)

    # create table for categories if it doesn't exist
    create_categories_table_query = """
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        description TEXT
    );
    """

    db.execute_query(create_categories_table_query)

    # create table for movements categories if it doesn't exist
    create_movements_categories_table_query = """
    CREATE TABLE IF NOT EXISTS movements_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movement_id INTEGER,
        category_id INTEGER,
        FOREIGN KEY (movement_id) REFERENCES movimientos(id),
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );
    """
    db.execute_query(create_movements_categories_table_query)
