from sklearn.linear_model import LogisticRegression

class Logistic_Regression(Model):
    def __init__(self, penalty, learning_rate, max_iter, lambd, tol, random_state, test_size, n_splits):
        super().__init__(random_state, test_size)
        self.learning_rate = learning_rate
        self.max_iter = max_iter
        self.penalty = penalty
        self.lambd = lambd
        self.tol = tol
        self.n_splits = n_splits

    def train(self, X_train, y_train):
        model = LogisticRegression(penalty=self.penalty, )
        model.fit(X_train, y_train)
        return model

    def run_logreg(self, X, y):
        print(self.run_cross_validation(X, y))