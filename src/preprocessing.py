import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from pathlib import Path

class Preprocessor():
    def __init__(self, df=None):
        conn = psycopg2.connect(
            dbname="wb",
            user="postgres",
            password='liza',
            host="localhost",
            port="5432"
        )
        if df is not None:
            self.df = df
        else:
            self.df = pd.read_sql('SELECT * FROM orders_master', conn)

    def analys_table(self):
        print(self.df.describe())
        print(self.df.columns)
        print(self.df['product_id'].nunique())
        print(self.df['customer_unique_id'].nunique())
        pd.set_option("display.width", None)
        print(self.df)

    def vizualize_histograms(self):
        count_category = self.df.groupby('product_category_name')['customer_unique_id'].count()
        count_customer = self.df.groupby('customer_unique_id')['product_category_name'].count()
        sns.histplot(count_customer)
        plt.title('Distribution of category')
        plt.savefig(Path(__file__).parent.parent / 'images/category_distribution.png')
        plt.show()
        sns.histplot(count_category)
        plt.title('Distribution of customers')
        plt.savefig(Path(__file__).parent.parent / 'images/customers_distribution.png')
        plt.show()
        self.df['review_score'].hist()
        plt.title('Distribution of Review Scores')
        plt.savefig(Path(__file__).parent.parent / 'images/review_score_distribution.png')
        plt.show()

    def check_outliers(self):
        print(self.df.isna())

    def drop_duplicates_items(self, customer_unique_id='customer_unique_id', product_id='product_id', timestamp='timestamp'):

        self.df.sort_values([customer_unique_id, timestamp], inplace=True)
        self.df['user_item'] = self.df[customer_unique_id].astype(str) + '_' + self.df[product_id].astype(str)

        while (self.df['user_item'].shift() == data['user_item']).sum() != 0:
            not_duplicates_ind = data['user_item'].shift() != data['user_item']
            data = data.loc[not_duplicates_ind]

        data = data.drop('user_item', axis=1)

        return data

    def filter_items(self, product_min_count, product_id='product_id'):
        """Фильтрация айтемов с малым количеством взаимодействий."""
        counts = self.df[product_id].value_counts()
        self.df = self.df[self.df[product_id].isin(counts[counts >= product_min_count].index)]


    def filter_users(self, customer_min_count, customer_unique_id='customer_unique_id'):
        """Фильтрация юзеров с малым количеством взаимодействий."""
        counts = self.df[customer_unique_id].value_counts()
        self.df = self.df[self.df[customer_unique_id].isin(counts[counts >= customer_min_count].index)]

    def preprocess(self):
        #self.analys_table()
        #self.vizualize_histograms()
        self.check_outliers()

