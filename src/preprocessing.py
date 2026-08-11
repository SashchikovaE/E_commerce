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
        #print(self.df.describe())
        print(self.df.columns)
        #print(self.df['customer_state'].nunique())
        #print(self.df['customer_city'].nunique())
        #pd.set_option("display.width", None)
        #print(self.df)

    def check_omissions(self):
        print(self.df.isna().sum())
        #print(self.df[self.df['order_approved_at'].isna()])
        #print(self.df[self.df['order_delivered_customer_date'].isna()])
        #print(self.df[self.df['customer_lat'].isna()])
        #print(self.df[self.df['product_category_name'].isna()])
        #print(self.df[self.df['product_weight_g'].isna()])
        #print(self.df[self.df['review_score'].isna()])
        #print(self.df[self.df['total_payment'].isna()])

    def fill_nan_dates(self):
        # 1. Колонки с датами
        date_cols = [
            'order_approved_at',
            'order_delivered_carrier_date',
            'order_delivered_customer_date',
            'order_estimated_delivery_date'
        ]
        # 2. Превращаем даты в дни (чтобы можно было усреднять)
        for col in date_cols:
            self.df[f'{col}_days'] = (self.df[col] - self.df['order_purchase_timestamp']).dt.days
        # 3. Маски для NaN
        nan_masks = {}
        for col in date_cols:
            nan_masks[col] = self.df[f'{col}_days'].isna()
        # 4. Заполняем по продавцу (как в coords — по городу)
        for col in date_cols:
            days_col = f'{col}_days'
            seller_avg = self.df.groupby('seller_id')[days_col].mean()
            self.df.loc[nan_masks[col], days_col] = self.df.loc[nan_masks[col], 'seller_id'].map(seller_avg)
        # 5. Если всё ещё NaN — заполняем по городу продавца (как в coords — по штату)
        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                city_avg = self.df.groupby('seller_city')[days_col].mean()
                self.df.loc[nan_mask, days_col] = self.df.loc[nan_mask, 'seller_city'].map(city_avg)
        # 6. Если всё ещё NaN — заполняем по штату продавца
        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                state_avg = self.df.groupby('seller_state')[days_col].mean()
                self.df.loc[nan_mask, days_col] = self.df.loc[nan_mask, 'seller_state'].map(state_avg)
        # 7. Если всё ещё NaN — глобальное среднее
        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                global_avg = self.df[days_col].mean()
                self.df.loc[nan_mask, days_col] = global_avg
        # 8. Возвращаем дни обратно в даты
        for col in date_cols:
            days_col = f'{col}_days'
            self.df[col] = self.df['order_purchase_timestamp'] + pd.to_timedelta(self.df[days_col], unit='D')
        # 9. Удаляем временные колонки с днями
        days_cols = [f'{col}_days' for col in date_cols]
        self.df = self.df.drop(columns=days_cols)

    def fill_nan_coords(self):
        coords_cols = [
            'customer_lat',
            'customer_lng',
        ]
        nan_lat_mask = self.df['customer_lat'].isna()
        nan_lng_mask = self.df['customer_lng'].isna()
        avg_customer_lat = self.df.groupby('customer_city')['customer_lat'].mean()
        avg_customer_lng = self.df.groupby('customer_city')['customer_lng'].mean()
        self.df.loc[nan_lat_mask, 'customer_lat'] = self.df.loc[nan_lat_mask, 'customer_city'].map(avg_customer_lat)
        self.df.loc[nan_lng_mask, 'customer_lng'] = self.df.loc[nan_lng_mask, 'customer_city'].map(avg_customer_lng)
        if self.df['customer_lat'].isna().any():
            nan_lat_mask = self.df['customer_lat'].isna()
            nan_lng_mask = self.df['customer_lng'].isna()
            avg_customer_lat = self.df.groupby('customer_state')['customer_lat'].mean()
            avg_customer_lng = self.df.groupby('customer_state')['customer_lng'].mean()
            self.df.loc[nan_lat_mask, 'customer_lat'] = self.df.loc[nan_lat_mask, 'customer_state'].map(avg_customer_lat)
            self.df.loc[nan_lng_mask, 'customer_lng'] = self.df.loc[nan_lng_mask, 'customer_state'].map(avg_customer_lng)

    def fill_nan_category(self):
        nan_category_mask = self.df['product_category_name'].isna()
        mode_category = self.df.groupby('customer_unique_id')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
        self.df.loc[nan_category_mask, 'product_category_name'] = self.df.loc[nan_category_mask, 'customer_unique_id'].map(mode_category)
        if self.df['product_category_name'].isna().any():
            nan_category_mask = self.df['product_category_name'].isna()
            mode_category = self.df.groupby('seller_id')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
            self.df.loc[nan_category_mask, 'product_category_name'] = self.df.loc[
                nan_category_mask, 'seller_id'].map(mode_category)
        if self.df['product_category_name'].isna().any():
            nan_category_mask = self.df['product_category_name'].isna()
            mode_category = self.df['product_category_name'].mode()[0]
            self.df.loc[nan_category_mask, 'product_category_name'] = mode_category

    def fill_nan_dimensions(self):
        'один товар. продавец забыл указать'
        cols = ['product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']
        for col in cols:
            nan_mask = self.df[col].isna()
            means = self.df.groupby('customer_unique_id')[col].mean()
            self.df.loc[nan_mask, col] = self.df.loc[nan_mask, 'customer_unique_id'].map(means)
        for col in cols:
            if self.df[col].isna().any():
                nan_mask = self.df[col].isna()
                means = self.df.groupby('customer_city')[col].mean()
                self.df.loc[nan_mask, col] = self.df.loc[nan_mask, 'customer_city'].map(means)
        for col in cols:
            if self.df[col].isna().any():
                nan_mask = self.df[col].isna()
                means = self.df.groupby('customer_state')[col].mean()
                self.df.loc[nan_mask, col] = self.df.loc[nan_mask, 'customer_state'].map(means)

    def fill_nan_review(self):
        nan_review_mask = self.df['review_score'].isna()
        avg_review_customer = self.df.groupby('customer_unique_id')['review_score'].mean()
        self.df.loc[nan_review_mask, 'review_score'] = self.df.loc[nan_review_mask, 'customer_unique_id'].map(avg_review_customer)
        if self.df['review_score'].isna().any():
            avg_review_customer = self.df.groupby('customer_city')['review_score'].mean()
            self.df.loc[nan_review_mask, 'review_score'] = self.df.loc[nan_review_mask, 'customer_city'].map(
                avg_review_customer)
        if self.df['review_score'].isna().any():
            avg_review_customer = self.df.groupby('customer_state')['review_score'].mean()
            self.df.loc[nan_review_mask, 'review_score'] = self.df.loc[nan_review_mask, 'customer_state'].map(
                avg_review_customer)

    def fill_nan_review_replies(self):
        self.df['has_review_message'] = self.df['review_comment_message'].notna().astype(int)
        nan_review_comment_mask = self.df['review_answer_timestamp'].isna()
        self.df.loc[nan_review_comment_mask, 'review_creation_date'] = self.df.loc[nan_review_comment_mask, 'order_delivered_customer_date']
        self.df.loc[nan_review_comment_mask, 'review_answer_timestamp'] = (
                self.df.loc[nan_review_comment_mask, 'order_delivered_customer_date'] + pd.Timedelta(days=999))

    def fill_nan_payment(self):
        nan_pay_mask = self.df['total_payment'].isna()
        if nan_pay_mask.sum() == 0:
            return
        bad_review_df = self.df[self.df['review_score'] == 1.0]
        type_mode = bad_review_df['payment_type'].mode()[0]
        sequential_mode = bad_review_df['payment_sequential'].mode()[0]
        installments_mode = bad_review_df['payment_installments'].mode()[0]
        self.df.loc[nan_pay_mask, 'total_payment'] = (
                self.df.loc[nan_pay_mask, 'freight_value'] +
                self.df.loc[nan_pay_mask, 'price']
        )
        self.df.loc[nan_pay_mask, 'payment_type'] = type_mode
        self.df.loc[nan_pay_mask, 'payment_sequential'] = sequential_mode
        self.df.loc[nan_pay_mask, 'payment_installments'] = installments_mode

    def fill_nan(self):
        self.df = self.df[self.df['order_status'] != 'canceled']
        self.df = self.df[self.df['order_status'] != 'unavailable']
        self.df = self.df.dropna(subset=['product_id'])
        self.fill_nan_coords()
        self.fill_nan_dates()
        self.fill_nan_category()
        self.fill_nan_dimensions()
        self.fill_nan_payment()
        self.fill_nan_review()
        self.fill_nan_review_replies()

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
        order_level = self.df.groupby(['customer_unique_id', 'order_id'], as_index=False).agg(
            order_item_id=('order_item_id', 'count'),
            product_category_name=('product_category_name', 'nunique'),
            product_dimensions=('product_dimensions', 'mean'),
            product_weight_g=('product_weight_g', 'mean'),
            seller_city=('seller_city', 'first'),
            seller_state=('seller_state', 'first'),
            seller_customer_distance=('seller_customer_distance', 'mean'),
            seller_delay=('seller_delay', 'mean'),
            price_sum=('price', 'sum'),
            price_mean=('price', 'mean'),
            freight_value=('freight_value', 'mean'),
            customer_city=('customer_city', 'first'),
            customer_state=('customer_state', 'first'),
            order_approval_time=('order_approval_time', 'first'),
            order_delivery_time=('order_delivery_time', 'first'),
            order_delay_time=('order_delay_time', 'first'),
            payment_type=('payment_type', 'first'),
            payment_installments=('payment_installments', 'first'),
            review_score=('review_score', 'first'),
            delivery_review_time=('delivery_review_time', 'mean')
        )

        print(order_level.columns.tolist())
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
            total_amount=('price_sum', 'sum'),
            avg_price=('price_mean', 'mean'),
            avg_freight_value=('freight_value', 'mean'),
            number_payment_type=('payment_type', 'nunique'),
            avg_payment_installments=('payment_installments', 'mean'),
            avg_review_score=('review_score', 'mean'),
            avg_delivery_review_time=('delivery_review_time', 'mean')
        )
        customer_level['will_return'] = (customer_level['order_count'] > 1).astype(int)

    def label_code(self, cols, mapping):
        for col in cols:
            self.df[col] = self.df[col].map(mapping)

    #def one_hot_code(self):

    #def normalize(self):


    def preprocess(self):
        self.analys_table()
        self.check_omissions()
        self.fill_nan()
        self.add_new_features()
        self.analys_table()
        self.group_data()
        self.check_omissions()
        #self.label_code(cols, mapping)
        #self.one_hot_code()
        #self.normalize()


