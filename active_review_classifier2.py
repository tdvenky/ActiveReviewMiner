import argparse
from random import shuffle

from sklearn import metrics
from sklearn import svm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from review_reader import ReviewReader


class ActiveReviewClassifier:
    def __init__(self, review_type, initial_train_size, algorithm, minimum_test_set_size, train_increment_size):
        self.review_type = review_type
        self.initial_train_size = initial_train_size
        self.algorithm = algorithm
        self.minimum_test_set_size = minimum_test_set_size
        self.train_increment_size = train_increment_size

        username, password, host, database_name = ActiveReviewClassifier.get_db_credentials()
        database = ReviewReader(username, password, host, database_name)
        self.reviews_pos_cls, self.reviews_neg_cls = database.get_app_reviews(self.review_type)
        database.close()

    @staticmethod
    def get_db_credentials():
        config_file = open("credentials.config", "r")  # Filename should be a constant
        lines = config_file.readlines()
        username = lines[0].split("=")[1].strip()
        password = lines[1].split("=")[1].strip()
        host = lines[2].split("=")[1].strip()
        database_name = lines[3].split("=")[1].strip()
        config_file.close()
        return username, password, host, database_name

    def run_experiments(self):
        shuffle(self.reviews_pos_cls)  # Shuffle data first
        shuffle(self.reviews_neg_cls)  # Shuffle data first

        initial_training_reviews_features, initial_training_reviews_classes, \
        initial_test_reviews_features, initial_test_reviews_classes = self.get_initial_data()

        print('Initial train size: ',  len(initial_training_reviews_features), len(initial_training_reviews_classes))
        print('Initial test size: ', len(initial_test_reviews_features), len(initial_test_reviews_classes))

        initial_test_reviews_predicted_classes, initial_test_reviews_predicted_class_probabilities = \
            self.classify_app_reviews(initial_training_reviews_features, initial_training_reviews_classes,
                                      initial_test_reviews_features)

        precision, recall, f1_score = self.calculate_classifier_performance_metrics(
            initial_test_reviews_classes, initial_test_reviews_predicted_classes)

        print('precision, recall, f1_score: ', precision, recall, f1_score)

    def get_initial_data(self):
        pos_cls_initial_size = int(self.initial_train_size/2)
        neg_cls_initial_size = int(self.initial_train_size - pos_cls_initial_size)

        initial_training_reviews = self.reviews_pos_cls[:pos_cls_initial_size] + \
                                   self.reviews_neg_cls[:neg_cls_initial_size]

        initial_training_classes = [1] * len(self.reviews_pos_cls[:pos_cls_initial_size]) + \
                                   [0] * len(self.reviews_neg_cls[:neg_cls_initial_size])

        initial_testing_reviews = self.reviews_pos_cls[pos_cls_initial_size:] + \
                                   self.reviews_neg_cls[neg_cls_initial_size:]

        initial_testing_classes = [1] * len(self.reviews_pos_cls[pos_cls_initial_size:]) + \
                                  [0] * len(self.reviews_neg_cls[neg_cls_initial_size:])

        initial_training_features, initial_test_features = self.vectorize_reviews(
            initial_training_reviews, initial_testing_reviews)

        return initial_training_features, initial_training_classes, initial_test_features, initial_testing_classes

    def vectorize_reviews(self, train_reviews, test_reviews):
        vectorizer = TfidfVectorizer(binary=True, use_idf=False, norm=None)  # Bag of words
        traing_reviews_features = vectorizer.fit_transform(train_reviews)
        test_reviews_features = vectorizer.transform(test_reviews)
        return traing_reviews_features, test_reviews_features

    def classify_app_reviews(self, train_reviews_features, train_reviews_classes, test_reviews_features):
        classifier = self.get_classifier()
        classifier.fit(train_reviews_features, train_reviews_classes)
        test_reviews_predicted_classes = classifier.predict(test_reviews_features)
        test_reviews_predicted_class_probabilities = classifier.predict_proba(test_reviews_features).tolist()
        return test_reviews_predicted_classes, test_reviews_predicted_class_probabilities

    def get_classifier(self):
        if self.algorithm == 'MultinomialNB':
            return MultinomialNB()
        elif self.algorithm == 'LogisticRegression':
            return LogisticRegression()
        elif self.algorithm == 'SVM':
            return svm.SVC(probability=True, kernel='linear')
        else:
            print('Classifier ' + self.algorithm + ' not supported')
            exit(-1)

    def calculate_classifier_performance_metrics(self, test_reviews_classes, predicted_test_reviews_classes):
        precision = metrics.precision_score(test_reviews_classes, predicted_test_reviews_classes)
        recall = metrics.recall_score(test_reviews_classes, predicted_test_reviews_classes)
        f1_score = metrics.f1_score(test_reviews_classes, predicted_test_reviews_classes)
        return precision, recall, f1_score


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', action="store", dest="review_type", help="Review Type", type=str)
    args = parser.parse_args()

    initial_train_size = 100
    algorithm = "MultinomialNB"
    minimum_test_set_size = 10
    train_increment_size = 20

    active_review_classifier = ActiveReviewClassifier(
        args.review_type, initial_train_size, algorithm, minimum_test_set_size, train_increment_size)

    active_review_classifier.run_experiments()
