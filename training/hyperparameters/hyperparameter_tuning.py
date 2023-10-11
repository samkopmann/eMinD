import getopt
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV
import pandas as pd
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
import glob
import json

def classifier_name(clf):
    return clf.__class__.__name__


param_grids = {
    "RandomForestClassifier": {
        'n_estimators': [10, 50, 100, 200, 500],
        'criterion': ['gini', 'entropy'],
        'max_depth': [None, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'min_samples_split': [2, 3, 4, 5, 6, 7, 8, 9],
    },
    "SVC": {
        'C': [0.1, 1, 10, 100, 1000, 10000],
        'gamma': [0.1, 0.01, 0.001, 0.0001],
        'kernel': ['rbf', 'poly', 'sigmoid'],
    },
    "DecisionTreeClassifier": {
        'criterion': ['gini', 'entropy'],
        'splitter': ['best', 'random'],
        'max_depth': [None, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        'min_samples_split': [2, 3, 4, 5, 6, 7, 8, 9],
        'min_samples_leaf': [1, 2, 3, 4, 5, 6, 7, 8, 9],
    }
}



#Parse command line arguments
training_parameters_file = ""
benign_data_file = ""
attack_data_file = ""

opts, args = getopt.getopt(sys.argv[1:], "b:a:", ["training_parameters_file=", "benign_data_file=", "attack_data_file="])
for opt, arg in opts:
    if opt in ("-b", "--benign_data_file"):
        benign_data_file = arg
    elif opt in ("-a", "--attack_data_file"):
        attack_data_file = arg
if benign_data_file == "" or attack_data_file == "":
    print("Usage: python hyperparameter_tuning.py -b <benign_data_file> -a <attack_data_file>")
    sys.exit(2)

# Load data


classifiers = [RandomForestClassifier(), SVC(), DecisionTreeClassifier()]
time_frames = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]
results = {}
for classifier in classifiers:
    results[classifier_name(classifier)] = {}
    for time_frame in time_frames:
        results[classifier_name(classifier)][time_frame] = {}

        #Load and concat all files in the directory "../../data/training/"
        #that match the naming scheme "attack_data_file_*_time_frame.csv"
        relevant_files = glob.glob(f'../../data/training/{attack_data_file}_*_{time_frame}.csv')
        data = pd.concat([pd.read_csv(f) for f in relevant_files])
        data["label"] = 1

        #Load and concat all files in the directory "../../data/training/"
        #that match the naming scheme "benign_data_file_*_time_frame.csv"
        relevant_files = glob.glob(f'../../data/training/{benign_data_file}_*_{time_frame}.csv')
        benign = pd.concat([pd.read_csv(f) for f in relevant_files])
        benign["label"] = 0

        data = pd.concat([data, benign])
        data.dropna(inplace=True)

        for column in data.columns:
            if column != "label":
                #Normalize data
                data[column] = (data[column] - data[column].min())
                max_min_diff = data[column].max() - data[column].min()
                if max_min_diff > 0:
                    data[column] = data[column] / max_min_diff

        gs = GridSearchCV(classifier, param_grids[classifier_name(classifier)], cv=10, n_jobs=-1, verbose=10)
        gs.fit(data.drop(["label"], axis=1), data["label"])
        results[classifier_name(classifier)][time_frame] = gs.best_params_

#Store results in "hyperparameter.json"
with open(f"hyperparameters_{benign_data_file}_{attack_data_file}.json", "w") as json_file:
    json.dump(results, json_file, indent=4)

