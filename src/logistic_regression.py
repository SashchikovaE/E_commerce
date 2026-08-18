from sklearn.linear_model import LogisticRegression
from model import Model
from sklearn.model_selection import GridSearchCV

class Logistic_Regression(Model):
    def __init__(self, penalty, solver, max_iter, lambd, tol, random_state, test_size, n_splits, class_weight):
        super().__init__(random_state, test_size, n_splits)
        self.penalty = penalty
        self.solver = solver
        self.max_iter = max_iter
        self.lambd = lambd
        self.tol = tol
        self.class_weight = class_weight

    def train_model(self, X_train, y_train):
        model = LogisticRegression(
            max_iter=self.max_iter,
            class_weight=self.class_weight,
            tol=self.tol
        )
        params = {
            'penalty': self.penalty,
            'solver': self.solver,
            'C': self.lambd,
        }
        grid_search = GridSearchCV(
            model,
            params,
            cv=5,
            scoring='roc_auc',
            n_jobs=-1,
            verbose=1
        )
        grid_search.fit(X_train, y_train)
        print(grid_search.best_estimator_)
        return grid_search.best_estimator_

    def predict_model(self, X_test, model):
        return model.predict(X_test)


    def run_logreg(self, X, y):
        print(self.run_cross_validation(X, y))