import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score
from sklearn.base import clone
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
import json
import datetime
import sys, getopt
import glob

def load_classifier(attack_data_file, benign_data_file, time_frame, classname):
    #load json
    with open(f'../hyperparameters/hyperparameters_{benign_data_file}_{attack_data_file}.json') as json_file:
        if classname == "MLPClassifier":
            return MLPClassifier(activation='relu', alpha= 0.001, hidden_layer_sizes=(25, 25), learning_rate="constant", learning_rate_init=0.0001, max_iter=5000, solver='adam')
        params  = json.load(json_file)[classname][str(time_frame)]
        if classname == "RandomForestClassifier":
            return RandomForestClassifier(criterion=params["criterion"], max_depth=params["max_depth"], min_samples_split=params["min_samples_split"], n_estimators=params["n_estimators"])
        elif classname == "SVC":
            return SVC(C=params["C"], gamma=params["gamma"], kernel=params["kernel"])
        elif classname == "DecisionTreeClassifier":
            return DecisionTreeClassifier(criterion=params["criterion"], max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"], min_samples_split=params["min_samples_split"], splitter=params["splitter"])



if __name__ == "__main__":

    #Parse command line arguments
    training_parameters_file = ""
    benign_data_file = ""
    attack_data_file = ""

    opts, args = getopt.getopt(sys.argv[1:], "t:b:a:", ["training_parameters_file=", "benign_data_file=", "attack_data_file="])
    for opt, arg in opts:
        if opt in ("-t", "--training_parameters_file"):
            training_parameters_file = arg
        elif opt in ("-b", "--benign_data_file"):
            benign_data_file = arg
        elif opt in ("-a", "--attack_data_file"):
            attack_data_file = arg
    if training_parameters_file == "" or benign_data_file == "" or attack_data_file == "":
        print("Usage: python training.py -t <training_parameters_file> -b <benign_data_file> -a <attack_data_file>")
        sys.exit(2)

    #Load training parameters
    with open(training_parameters_file) as json_file:
        training_parameters = json.load(json_file)
    time_frames = training_parameters["time_frames"]
    metrics = training_parameters["metrics"]
    runs = training_parameters["runs"]

    classifiers = ["RandomForestClassifier", "SVC", "DecisionTreeClassifier", "MLPClassifier"]

    #Initialize results dictionary
    results = {
    }
        
    for classifier in classifiers:
        results[classifier] = {}
        for time_frame in time_frames:
            results[classifier][time_frame] = {}
            for metric in metrics:
                results[classifier][time_frame][metric] = []

    #Run training
    for classifier in classifiers:
        print("Classifier: " + classifier)
        for time_frame in time_frames:
            print("Time frame: " + str(time_frame))

            base_clf = load_classifier(attack_data_file, benign_data_file, time_frame, classifier)

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

            for run in range(runs):
                train, test = train_test_split(data, test_size = training_parameters["test_split"], shuffle=True)
                train_x = train.drop(["label"], axis=1)
                train_y = train["label"]
                test_x = test.drop(["label"], axis=1)
                test_y = test["label"]
                clf = clone(base_clf)
                clf.fit(train_x, train_y)

                results[classifier][time_frame]["accuracy"].append(accuracy_score(test_y, clf.predict(test_x)))
                results[classifier][time_frame]["recall"].append(recall_score(test_y, clf.predict(test_x)))
                results[classifier][time_frame]["precision"].append(precision_score(test_y, clf.predict(test_x)))
                results[classifier][time_frame]["f1"].append(f1_score(test_y, clf.predict(test_x)))

    #Store results as json with caida and timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    with open(f'../results/{current_time}_{benign_data_file}_{attack_data_file}.json', 'w') as fp:
        json.dump(results, fp)


