import sys
import os
project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))
sys.path.append(project_root)
from preprocessing import Preprocessor
from logistic_regression import Logistic_Regression

if __name__ == "__main__":
    label_cols = ['order_status']
    one_hot_cols = ['payment_type', 'most_common_seller_state', 'customer_state']
    freq_cols = ['customer_city', 'most_common_seller_city', 'most_common_product_category_name']
    mapping = {
        'delivered': 6,
        'shipped': 5,
        'canceled': 4,
        'invoiced': 3,
        'processing': 2,
        'approved': 1,
        'created': 0
    }
    preprocessor = Preprocessor()
    preprocessor.preprocess(one_hot_cols, freq_cols)
    X = preprocessor.df.drop(['bad_review', 'order_id', 'customer_unique_id', 'product_id'], axis=1)
    y = preprocessor.df['bad_review']
    model = Logistic_Regression(
        penalty=['l2'],
        solver=['lbfgs', 'saga'],
        max_iter=50000,
        lambd=[0.1, 1, 10],
        tol=1e-5,
        random_state=42,
        test_size=0.3,
        n_splits=5,
        class_weight='balanced'
    )
    model.run_logreg(X, y)




