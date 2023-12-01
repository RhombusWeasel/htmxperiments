import sqlite3
import json
from utils.logger import Logger


class Database:
    def __init__(self, db_name, log_level=Logger.ERROR):
        self.db_name = db_name
        self.log = Logger(db_name, log_level=log_level)
        self.log.info(f"Database initialized: {db_name}")

    def get_conn(self):
        conn = sqlite3.connect(self.db_name)
        return conn

    def init_db(self, table_name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(
            f'''CREATE TABLE IF NOT EXISTS {table_name} (_id TEXT PRIMARY KEY UNIQUE, last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        self.log.info(f"Table initialized: {table_name}")

    def create_table(self, table_name):
        self.init_db(table_name)

    def column_exists(self, table_name, column_name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table_name})")
        columns = c.fetchall()
        conn.close()
        return any(col[1] == column_name for col in columns)

    def add_column_to_table(self, table_name, column_name, data_type):
        if self.column_exists(table_name, column_name):
            self.log.info(
                f"Column {column_name} exists in table {table_name}")
            return
        
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}")
        conn.commit()
        conn.close()
        self.log.info(f"Added column {column_name} to table {table_name}")

    def save_data(self, table_name, _id, column_name, data):
        if not self.column_exists(table_name, column_name):
            self.add_column_to_table(table_name, column_name, "TEXT")

        conn = self.get_conn()
        c = conn.cursor()

        # Check if _id exists in the table
        self.log.info(f"Checking if {_id} exists in database")
        c.execute(f"SELECT _id FROM {table_name} WHERE _id=?", (_id,))
        result = c.fetchone()

        if result:
            # Update the specified column for the existing _id and the last_login timestamp
            c.execute(
                f"UPDATE {table_name} SET {column_name}=?, last_update=CURRENT_TIMESTAMP WHERE _id=?", (
                    data, _id)
            )
        else:
            # Insert a new row with the _id and specified column data
            c.execute(
                f"INSERT INTO {table_name} (_id, {column_name}, last_update) VALUES (?, ?, CURRENT_TIMESTAMP)", (_id, data))

        conn.commit()
        conn.close()
        self.log.info(f"Saved data to database for ID {_id}")

    def load_data(self, table_name, _id, column_name='*'):
        try:
            conn = self.get_conn()
            c = conn.cursor()

            # Get column names
            c.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in c.fetchall()]

            # Get row data
            c.execute(f"SELECT * FROM {table_name} WHERE _id=?", (_id,))
            result = c.fetchone()
            conn.close()

            if result:
                # Map row data to column names and return as a dictionary
                row_data = dict(zip(columns, result))
                if column_name != '*':
                    return row_data[column_name]
                else:
                    return row_data
            else:
                self.log.info(f"Could not find data in database for ID {_id}")
                return None
        except Exception as e:
            self.log.error(f"Error loading data from database for ID {_id}")
            self.log.error(e)
            return None

    def get_id_list(self, table_name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(f"SELECT _id FROM {table_name}")
        result = c.fetchall()
        self.log.info(f"Loaded ID list from database for table {table_name}")
        self.log.data(result)
        conn.close()
        return [row[0] for row in result]

    def clear_db(self, table_name):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(f"DELETE FROM {table_name}")
        conn.commit()
        conn.close()
        self.log.info(f"Cleared table {table_name}")

    def delete_row(self, table_name, _id):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(f"DELETE FROM {table_name} WHERE _id=?", (_id,))
        conn.commit()
        conn.close()
        self.log.info(f"Deleted row from table {table_name} for ID {_id}")

    def custom_query(self, query):
        conn = self.get_conn()
        c = conn.cursor()
        c.execute(query)
        result = c.fetchall()
        conn.close()
        return result

    def get_table(self, table_name):
        conn = self.get_conn()
        c = conn.cursor()
        # Get every field unless it is called 'password'
        c.execute(
            f"SELECT name FROM PRAGMA_TABLE_INFO('{table_name}') WHERE name != 'password'")
        columns = c.fetchall()
        columns = [col[0] for col in columns]
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
        c.execute(query)
        result = c.fetchall()
        conn.close()
        # Assemble the columns and rows into a dictionary
        result = [dict(zip(columns, row)) for row in result]
        return result
