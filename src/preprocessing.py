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

    def check_cols_for_encode(self):
        # для енкода
        print(self.df['most_common_product_category_name'].nunique())
        print(self.df['payment_type'].unique())
        print(self.df['customer_state'].nunique())
        print(self.df['customer_city'].nunique())
        print(self.df['most_common_seller_state'].nunique())
        print(self.df['most_common_seller_city'].nunique())
        print(self.df['product_name_length'].nunique())
        print(self.df['product_description_length'].nunique())

    def check_order_status(self):
        pd.set_option("display.width", None)
        # чекнуть че такое кэнслд (чювак не оплатил)
        # unavailable это тупа удаленные
        print(self.df[self.df['order_status'] == 'canceled'])
        print(self.df[self.df['order_status'] == 'unavailable'])

    def analys_table(self):
        #print(self.df.describe())
        print(self.df.columns)
        pd.set_option("display.width", None)
        print(self.df)

    def check_omissions(self):
        print(self.df.isna().sum())
        print(self.df[self.df['order_approved_at'].isna()])
        print(self.df[self.df['order_delivered_customer_date'].isna()])
        print(self.df[self.df['customer_lat'].isna()])
        print(self.df[self.df['product_category_name'].isna()])
        print(self.df[self.df['product_weight_g'].isna()])
        print(self.df[self.df['review_score'].isna()])
        print(self.df[self.df['total_payment'].isna()])
        print(self.df[self.df['product_name_lenght'].isna()])
        print(self.df[self.df['product_description_lenght'].isna()])

    def fill_nan_dates(self):
        date_cols = [
            'order_approved_at',
            'order_delivered_carrier_date',
            'order_delivered_customer_date',
            'order_estimated_delivery_date'
        ]
        for col in date_cols:
            self.df[f'{col}_days'] = (self.df[col] - self.df['order_purchase_timestamp']).dt.days

        nan_masks = {}
        for col in date_cols:
            nan_masks[col] = self.df[f'{col}_days'].isna()

        for col in date_cols:
            days_col = f'{col}_days'
            seller_avg = self.df.groupby('seller_id')[days_col].mean()
            self.df.loc[nan_masks[col], days_col] = self.df.loc[nan_masks[col], 'seller_id'].map(seller_avg)

        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                city_avg = self.df.groupby('seller_city')[days_col].mean()
                self.df.loc[nan_mask, days_col] = self.df.loc[nan_mask, 'seller_city'].map(city_avg)

        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                state_avg = self.df.groupby('seller_state')[days_col].mean()
                self.df.loc[nan_mask, days_col] = self.df.loc[nan_mask, 'seller_state'].map(state_avg)

        for col in date_cols:
            days_col = f'{col}_days'
            if self.df[days_col].isna().any():
                nan_mask = self.df[days_col].isna()
                global_avg = self.df[days_col].mean()
                self.df.loc[nan_mask, days_col] = global_avg

        for col in date_cols:
            days_col = f'{col}_days'
            self.df[col] = self.df['order_purchase_timestamp'] + pd.to_timedelta(self.df[days_col], unit='D')

        days_cols = [f'{col}_days' for col in date_cols]
        self.df = self.df.drop(columns=days_cols)

    def fill_nan_product_info(self):
        prod_cols = [
            'product_description_lenght',
            'product_name_lenght'
        ]
        for i in prod_cols:
            nan_i_mask = self.df[i].isna()
            avg_i = self.df.groupby('seller_id')[i].mean()
            self.df.loc[nan_i_mask, i] = self.df.loc[nan_i_mask, 'seller_id'].map(avg_i)
            if self.df[i].isna().any():
                nan_i_mask = self.df[i].isna()
                avg_i = self.df.groupby('seller_city')[i].mean()
                self.df.loc[nan_i_mask, i] = self.df.loc[nan_i_mask, 'seller_city'].map(
                    avg_i)
            if self.df[i].isna().any():
                nan_i_mask = self.df[i].isna()
                avg_i = self.df.groupby('seller_state')[i].mean()
                self.df.loc[nan_i_mask, i] = self.df.loc[nan_i_mask, 'seller_state'].map(
                    avg_i)
            if self.df[i].isna().any():
                nan_i_mask = self.df[i].isna()
                avg_i = self.df[i].mean()
                self.df.loc[nan_i_mask, i] = avg_i
                #self.df.loc[nan_name_mask, 'customer_lng'] = self.df.loc[nan_name_mask, 'customer_state'].map(
                #    avg_customer_lng)

    def fill_nan_coords(self):
        coords_cols = [
            'customer_lat',
            'customer_lng',
        ]
        for i in coords_cols:
            nan_coord_mask = self.df[i].isna()
            #nan_lng_mask = self.df['customer_lng'].isna()
            avg_coord = self.df.groupby('customer_city')[i].mean()
            #avg_customer_lng = self.df.groupby('customer_city')['customer_lng'].mean()
            self.df.loc[nan_coord_mask, i] = self.df.loc[nan_coord_mask, 'customer_city'].map(avg_coord)
            #self.df.loc[nan_lng_mask, 'customer_lng'] = self.df.loc[nan_lng_mask, 'customer_city'].map(avg_customer_lng)
            if self.df[i].isna().any():
                nan_coord_mask = self.df[i].isna()
                #nan_lng_mask = self.df['customer_lng'].isna()
                avg_coord = self.df.groupby('customer_state')[i].mean()
                #avg_customer_lng = self.df.groupby('customer_state')['customer_lng'].mean()
                self.df.loc[nan_coord_mask, i] = self.df.loc[nan_coord_mask, 'customer_state'].map(avg_coord)
                #self.df.loc[nan_lng_mask, 'customer_lng'] = self.df.loc[nan_lng_mask, 'customer_state'].map(avg_customer_lng)

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
            mode_category = self.df.groupby('seller_city')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
            self.df.loc[nan_category_mask, 'product_category_name'] = self.df.loc[
                nan_category_mask, 'seller_city'
            ].map(mode_category)
        if self.df['product_category_name'].isna().any():
            nan_category_mask = self.df['product_category_name'].isna()
            mode_category = self.df.groupby('seller_state')['product_category_name'].agg(lambda x: x.mode()[0] if len(x.mode()) > 0 else None)
            self.df.loc[nan_category_mask, 'product_category_name'] = self.df.loc[
                nan_category_mask, 'seller_state'
            ].map(mode_category)

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
        self.df = self.df[self.df['order_status'] == 'delivered']
        self.df = self.df.dropna(subset=['product_id'])
        self.fill_nan_coords()
        self.fill_nan_dates()
        self.fill_nan_category()
        self.fill_nan_product_info()
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
        self.df['order_approval_time_h'] = (self.df['order_approved_at'] - self.df['order_purchase_timestamp']).dt.total_seconds() / 3600
        self.df['order_delivery_time'] = (self.df['order_delivered_customer_date'] - self.df['order_purchase_timestamp']).dt.days
        self.df['order_delay_time'] = (self.df['order_delivered_customer_date'] - self.df['order_estimated_delivery_date']).dt.days
        self.df['product_dimensions'] = self.df['product_length_cm'] * self.df['product_height_cm'] * self.df['product_width_cm']
        self.df['seller_delay'] = (self.df['order_delivered_customer_date'] - self.df['shipping_limit_date']).dt.days
        self.df['seller_customer_distance'] = self.df.apply(lambda row: self.haversine(row['customer_lat'], row['customer_lng'],
                                                            row['seller_lat'], row['seller_lng']),
                                                            axis=1)
        self.df['delivery_review_time'] = (self.df['review_creation_date'] - self.df['order_delivered_customer_date']).dt.days
        self.df['review_to_answer_time_h'] = (self.df['review_answer_timestamp'] - self.df['review_creation_date']).dt.total_seconds() / 3600
        self.df = self.df.drop([
            'order_purchase_timestamp',
            'order_approved_at',
            'order_delivered_carrier_date',
            'order_delivered_customer_date',
            'order_estimated_delivery_date',
            'product_length_cm',
            'product_height_cm',
            'product_width_cm',
            'shipping_limit_date',
            'review_creation_date',
            'review_answer_timestamp',
            'seller_lat',
            'seller_lng',
            'customer_lat',
            'customer_lng'
            ], axis=1)

    def group_data(self):
        order_level = self.df.groupby(['order_id'], as_index=False).agg(
            count_order_item_id=('order_item_id', 'count'),
            customer_unique_id=('customer_unique_id', 'first'),
            #order_status=('order_status', 'first'),

            # product info
            product_id=('product_id', 'first'),
            product_description_length=('product_description_lenght', 'first'),
            product_name_length=('product_name_lenght', 'first'),
            nunique_product_category_name=('product_category_name', 'nunique'),
            most_common_product_category_name=('product_category_name', lambda x: x.mode()[0] if len(x.mode()) > 0 else None),
            avg_product_dimensions=('product_dimensions', 'mean'),
            avg_product_weight_g=('product_weight_g', 'mean'),

            # geo
            customer_city=('customer_city', 'first'),
            customer_state=('customer_state', 'first'),
            most_common_seller_city=('seller_city', lambda x: x.mode()[0] if len(x.mode()) > 0 else None),
            most_common_seller_state=('seller_state', lambda x: x.mode()[0] if len(x.mode()) > 0 else None),
            avg_seller_customer_distance=('seller_customer_distance', 'mean'),

            # price
            total_price=('price', 'sum'),
            avg_price=('price', 'mean'),
            avg_freight_value=('freight_value', 'mean'),

            # payment info
            payment_type=('payment_type', 'first'),
            payment_installments=('payment_installments', 'first'),

            # order timing
            order_approval_time_h=('order_approval_time_h', 'first'),
            order_delivery_time=('order_delivery_time', 'first'),
            order_delay_time=('order_delay_time', 'first'),
            avg_seller_delay=('seller_delay', 'mean'),

            #review
            #avg_delivery_review_time=('delivery_review_time', 'mean'),
            #review_to_answer_time_h=('review_to_answer_time_h', 'first'),
            review_score=('review_score', 'first'),
            )
        order_level['bad_review'] = (order_level['review_score'] < 4).astype(int)
        order_level = order_level.drop(['review_score'], axis=1)
        self.df = order_level

    def label_code(self, cols, mapping):
        for col in cols:
            self.df[col] = self.df[col].map(mapping)

    def one_hot_code(self, cols):
        for col in cols:
            dummies = pd.get_dummies(self.df[col], prefix=col, drop_first=True)
            dummies = dummies.astype(int)
            self.df = pd.concat([self.df.drop(col, axis=1), dummies], axis=1, ignore_index=False)

    def frequency_encode(self, cols):
        for col in cols:
            freq = self.df[col].value_counts()
            self.df[f'{col}_freq'] = self.df[col].map(freq)
            self.df = self.df.drop(col, axis=1)

    def vizualize_correlation_matrix(self):
        numeric_cols = self.df.select_dtypes(include=['number'])
        pd.set_option('display.width', None)
        print(numeric_cols)
        print(self.df['bad_review'].dtype)
        plt.figure(figsize=(28.8, 19.2))
        sns.heatmap(numeric_cols.corr(), annot=True, fmt=".2f")
        plt.title('Correlation matrix')
        file = Path(__file__).parent.parent / 'images/correlation_matrix.png'
        file.parent.mkdir(exist_ok=True)
        plt.savefig(file)
        plt.show()

    def vizualize_target_dictribution(self):
        plt.plot(self.df['bad_review'])
        sns.countplot(data=self.df, x='bad_review')
        file = Path(__file__).parent.parent / 'images/target_distribution.png'
        plt.savefig(file)
        print(self.df['bad_review'].value_counts())

    def normalize(self):
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        non_binary_cols = [
            col for col in numeric_cols if self.df[col].nunique() > 2]
        mean = self.df[non_binary_cols].mean(axis=0)
        std = self.df[non_binary_cols].std(axis=0)
        self.df[non_binary_cols] = (self.df[non_binary_cols] - mean) / (std + 1e-10)

    def preprocess(self, one_hot_cols, freq_cols):
        self.analys_table()
        #self.check_order_status()
        self.check_omissions()
        self.fill_nan()
        self.add_new_features()
        self.group_data()
        #self.check_omissions()
        self.check_cols_for_encode()
        self.vizualize_correlation_matrix()
        self.vizualize_target_dictribution()
        self.one_hot_code(one_hot_cols)
        self.frequency_encode(freq_cols)
        self.normalize()
        self.analys_table()
