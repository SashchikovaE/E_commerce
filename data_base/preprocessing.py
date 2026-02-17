import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import psycopg2

class Preprocessor():
    def __init__(self, df=None):
        conn = psycopg2.connect(
            dbname="ecommerce",
            user="postgres",
            password="123",
            host="localhost",
            port="5432"
        )
        if df is None:
            self.df = df
        else:
            self.df = pd.read_sql('SELECT * FROM orders_master', conn)

    #def analysis_outliers(self):
