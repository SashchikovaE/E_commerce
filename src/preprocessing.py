import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import psycopg2
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

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
        pd.set_option("display.width", None)
        print(self.df[self.df['product_id'].isna()])
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

    def check_omissions(self):
        print(self.df.isna().sum())

    def fill_nan_by_status(self):
        time_cols = [
            'order_approval_time',
            'order_delivery_time',
            'order_delay_time',
            'seller_delay',
            'delivery_review_time'
        ]
        in_progress_mask = ~self.df['order_status'].isin(['delivered'])
        delivered_mask = self.df['order_status'] == 'delivered'

        seller_avg = self.df[delivered_mask].groupby('seller_id')[time_cols].mean().add_prefix('seller_avg_')
        self.df = self.df.merge(seller_avg, on='seller_id', how='left')

        city_avg = self.df[delivered_mask].groupby('seller_city')[time_cols].mean().add_prefix('city_avg_')
        self.df = self.df.merge(city_avg, on='seller_city', how='left')

        state_avg = self.df[delivered_mask].groupby('seller_state')[time_cols].mean().add_prefix('state_avg_')
        self.df = self.df.merge(state_avg, on='seller_state', how='left')

        global_avg = self.df[delivered_mask][time_cols].mean()

        for col in time_cols:
            self.df.loc[in_progress_mask, col] = self.df.loc[in_progress_mask, f'client_avg_{col}']
            still_nan = in_progress_mask & self.df[col].isna()
            self.df.loc[still_nan, col] = self.df.loc[still_nan, f'city_avg_{col}']
            still_nan = in_progress_mask & self.df[col].isna()
            self.df.loc[still_nan, col] = self.df.loc[still_nan, f'state_avg_{col}']
            still_nan = in_progress_mask & self.df[col].isna()
            self.df.loc[still_nan, col] = global_avg[col]

        self.df['is_estimated'] = 0
        self.df.loc[in_progress_mask, 'is_estimated'] = 1

        agg_cols = [col for col in self.df.columns if col.startswith(('seller_avg_', 'city_avg_', 'state_avg_'))]
        self.df = self.df.drop(columns=agg_cols)

    def fill_nan_coords(self):
        coords_cols = [
            'customer_lat',
            'customer_lng',
        ]
        lat_nan_mask = self.df['customer_lat'].isna()
        lng_nan_mask = self.df['customer_lng'].isna()
        avg_customer_lat = self.df.groupby('customer_city')['customer_lat'].mean()
        avg_customer_lng = self.df.groupby('customer_city')['customer_lng'].mean()
        self.df.loc[lat_nan_mask, 'customer_lat'] = self.df.loc[lat_nan_mask, 'customer_city'].map(avg_customer_lat)
        self.df.loc[lng_nan_mask, 'customer_lng'] = self.df.loc[lng_nan_mask, 'customer_city'].map(avg_customer_lng)
        if self.df['customer_lat'].isna().any():
            lat_nan_mask = self.df['customer_lat'].isna()
            lng_nan_mask = self.df['customer_lng'].isna()
            avg_customer_lat = self.df.groupby('customer_state')['customer_lat'].mean()
            avg_customer_lng = self.df.groupby('customer_state')['customer_lng'].mean()
            self.df.loc[lat_nan_mask, 'customer_lat'] = self.df.loc[lat_nan_mask, 'customer_state'].map(avg_customer_lat)
            self.df.loc[lng_nan_mask, 'customer_lng'] = self.df.loc[lng_nan_mask, 'customer_state'].map(avg_customer_lng)

    def fill_nan_category(self):
        category_nan_mask = self.df['product_category_name'].isna()
        mode_category = self.df.groupby('customer_unique_id')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
        self.df.loc[category_nan_mask, 'product_category_name'] = self.df.loc[category_nan_mask, 'customer_unique_id'].map(mode_category)
        if self.df['product_category_name'].isna().any():
            category_nan_mask = self.df['product_category_name'].isna()
            mode_category = self.df.groupby('seller_id')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
            self.df.loc[category_nan_mask, 'product_category_name'] = self.df.loc[
                category_nan_mask, 'seller_id'].map(mode_category)
        if self.df['product_category_name'].isna().any():
            category_nan_mask = self.df['product_category_name'].isna()
            mode_category = self.df['product_category_name'].mode()[0]
            self.df.loc[category_nan_mask, 'product_category_name'] = mode_category


    #def fill_nan_dimensions(self):


    #def fill_nan_review(self):


    def fill_nan_payment(self):
        not_pay_mask = self.df['total_payment'].isna()
        if not_pay_mask.sum() == 0:
            return
        bad_review_df = self.df[self.df['review_score'] == 1.0]
        type_mode = bad_review_df['payment_type'].mode()[0]
        sequential_mode = bad_review_df['payment_sequential'].mode()[0]
        installments_mode = bad_review_df['payment_installments'].mode()[0]
        self.df.loc[not_pay_mask, 'total_payment'] = (
                self.df.loc[not_pay_mask, 'freight_value'] +
                self.df.loc[not_pay_mask, 'price']
        )
        self.df.loc[not_pay_mask, 'payment_type'] = type_mode
        self.df.loc[not_pay_mask, 'payment_sequential'] = sequential_mode
        self.df.loc[not_pay_mask, 'payment_installments'] = installments_mode

    def fill_nan(self):
        self.df = self.df[self.df['order_status'] != 'canceled']
        self.df = self.df[self.df['order_status'] != 'unavailable']
        self.df = self.df.dropna(subset=['product_id'])
        self.fill_nan_coords()
        #self.fill_nan_by_status()
        self.fill_nan_category()
        #self.fill_nan_dimensions()
        self.fill_nan_payment()
        #self.fill_nan_review()

    def haversine(self, seller_lat, seller_lng, customer_lat, customer_lng):
        R = 6371
        seller_lat, seller_lng, customer_lat, customer_lng = map(radians, [seller_lat, seller_lng, customer_lat, customer_lng])
        dlat = customer_lat - seller_lat
        dlng = customer_lng - seller_lng
        a = sin(dlat / 2) ** 2 + cos(seller_lat) * cos(customer_lat) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def add_new_features(self):
        self.df['order_approval_time'] = (self.df['order_approved_at'] - self.df['order_purchase_timestamp']).dt.days
        self.df['order_delivery_time'] = (self.df['order_delivered_customer_date'] - self.df['order_purchase_timestamp']).dt.days
        self.df['order_delay_time'] = (self.df['order_delivered_customer_date'] - self.df['order_estimated_delivery_date']).dt.days
        self.df['product_dimensions'] = self.df['product_length_cm'] * self.df['product_height_cm'] * self.df['product_width_cm']
        self.df['seller_delay'] = (self.df['order_delivered_customer_date'] - self.df['shipping_limit_date']).dt.days
        self.df['seller_customer_distance'] = self.df.apply(lambda row: self.haversine(row['customer_lat'], row['customer_lng'],
                                                            row['seller_lat'], row['seller_lng']),
                                                            axis=1)
        self.df['delivery_review_time'] = (self.df['review_creation_date'] - self.df['order_delivered_customer_date']).dt.days

    def group_data(self):
        order_level = self.df.groupby(['customer_unique_id', 'order_id']).agg({
            'order_item_id': 'count',
            'product_category_name': 'nunique',
            'product_dimensions': 'mean',
            'product_weight_g': 'mean',
            'seller_city': 'first',
            'seller_state': 'first',
            'seller_customer_distance': 'mean',
            'seller_delay': 'mean',
            'price': ['sum', 'mean'],
            'freight_value': 'mean',
            'customer_city': 'first',
            'customer_state': 'first',
            'order_approval_time': 'first',
            'order_delivery_time': 'first',
            'order_delay_time': 'first',
            'payment_type': 'first',
            'payment_installments': 'first',
            'review_score': 'first',
            'delivery_review_time': 'mean'
        }).reset_index()
        customer_level = order_level.groupby('customer_unique_id', as_index=False).agg(
            order_count=('order_id', 'count'),
            customer_city=('customer_city', 'first'),
            customer_state=('customer_state', 'first'),
            avg_time_approval=('order_approval_time', 'mean'),
            avg_delivery_time=('order_delivery_time', 'mean'),
            avg_delay_time=('order_delay_time', 'mean'),
            avg_item_count=('order_item_id', 'mean'),
            avg_number_category=('product_category_name', 'mean'),
            avg_product_dimension=('product_dimensions', 'mean'),
            avg_product_weight=('product_weight_g', 'mean'),
            most_common_seller_city=('seller_city', lambda x: x.mode()[0]),
            most_common_seller_state=('seller_state', lambda x: x.mode()[0]),
            avg_seller_customer_distance=('seller_customer_distance', 'mean'),
            avg_seller_delay=('seller_delay', 'mean'),
            total_amount=('price', 'sum'),
            avg_price=('price', 'mean'),
            avg_freight_value=('freight_value', 'mean'),
            number_payment_type=('payment_type', 'nunique'),
            avg_payment_installments=('payment_installments', 'mean'),
            avg_review_score=('review_score', 'mean'),
            avg_delivery_review_time=('delivery_review_time', 'mean')
        )

    def preprocess(self):
        self.analys_table()
        #self.vizualize_histograms()
        self.check_omissions()
        #self.add_new_features()
        self.fill_nan()
        #self.group_data()
        self.check_omissions()


