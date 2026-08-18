from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import numpy as np
from sklearn.model_selection import KFold

class Model:
    def __init__(self, random_state, test_size, n_splits):
        self.random_state = random_state
        self.test_size = test_size
        self.n_splits = n_splits

    def cross_validation(self, X, y):
        kf = KFold(n_splits=self.n_splits, shuffle=True, random_state=self.random_state)
        for train_index, test_index in kf.split(X):
            X_train = X.iloc[train_index]
            y_train = y.iloc[train_index]
            X_test = X.iloc[test_index]
            y_test = y.iloc[test_index]
            yield X_train, y_train, X_test, y_test

    def train_and_evaluate(self, X_train, y_train, X_test, y_test):
        model = self.train_model(X_train, y_train)
        y_pred = self.predict_model(X_test, model)
        return self.calculate_metrics(y_test, y_pred)

    def train_model(self, X_train, y_train):
        raise NotImplementedError

    def predict_model(self, X_test):
        raise NotImplementedError

    def calculate_metrics(self, y_test, y_pred):
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'ROC-AUC': roc_auc_score(y_test, y_pred)
        }
        return metrics

    def average_metrics(self, metrics):
        metric_names = ['accuracy', 'precision', 'recall', 'f1', 'ROC-AUC']
        return {
            metric: np.mean([m[metric] for m in metrics]) for metric in metric_names
        }


    def run_cross_validation(self, X, y):
        metrics = []
        for X_train, y_train, X_test, y_test in self.cross_validation(X, y):
            metrics.append(self.train_and_evaluate(X_train, y_train, X_test, y_test))
        return self.average_metrics(metrics)
        #return metrics