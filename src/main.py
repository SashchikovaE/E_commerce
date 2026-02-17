import sys
import os
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
sys.path.append(project_root)
from data_base.connection import DataBase

if __name__ == "__main__":
    db = DataBase("e-commerce", "liza", "postgress")
    db.connect()
    #print(db.execute_query('initial_queries.sql'))
    db.close()
