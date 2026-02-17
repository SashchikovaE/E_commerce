import pandas as pd
import psycopg2

class DataBase:

    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.params = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(**self.params)
        return self.conn

    def execute_query(self, query):
        with open(query, 'r', encoding='utf-8') as file:
            query_txt = file.read()
        df = pd.read_sql_query(query_txt, self.conn)
        return df

    def close(self):
        self.conn.close()
