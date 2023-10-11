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
    benign_data_file = ""
    attack_data_file = ""
    time_frame = 0

    classifiers = ["RandomForestClassifier", "SVC", "DecisionTreeClassifier", "MLPClassifier"]
    features = ["Packet count","TCP count","UDP count","Mean IAT","IAT var",
                "Unique src IPs","Unique dst IPs","Unique src ports","Unique dst ports",
                "SYN count","FIN count","Mean packet length","Packet length var"]
    metrics = ["accuracy", "recall", "precision", "f1"]
    runs = 100

    opts, args = getopt.getopt(sys.argv[1:], "t:b:a:", ["timeframe=", "benign_data_file=", "attack_data_file="])
    for opt, arg in opts:
        if opt in ("-t", "--timeframe"):
            time_frame = float(arg)
        elif opt in ("-b", "--benign_data_file"):
            benign_data_file = arg
        elif opt in ("-a", "--attack_data_file"):
            attack_data_file = arg
    if benign_data_file == "" or attack_data_file == "" or time_frame == 0:
        print("Usage: python feature_importance.py -b <benign_data_file> -a <attack_data_file> -t <time_frame>")
        sys.exit(2)



    results = {
    }
        
    for classifier in classifiers:
        results[classifier] = {}
        for feature in features:
            results[classifier][feature] = {}
            for metric in metrics:
                results[classifier][feature][metric] = []


    for classifier in classifiers:
        print("Classifier: " + classifier)
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
            train, test = train_test_split(data, test_size = 0.3, shuffle=True)
            train_x = train.drop(["label"], axis=1)
            train_y = train["label"]
            test_x = test.drop(["label"], axis=1)
            test_y = test["label"]
            clf = clone(base_clf)
            clf.fit(train_x, train_y)
            acc_all, rec_all, prec_all, f1_all = accuracy_score(test_y, clf.predict(test_x)), recall_score(test_y, clf.predict(test_x)), precision_score(test_y, clf.predict(test_x)), f1_score(test_y, clf.predict(test_x))
            for feature in features:
                test_x_copy = test_x.copy()
                test_x_copy[feature] = np.random.permutation(test_x_copy[feature].values)
                acc, rec, prec, f1 = accuracy_score(test_y, clf.predict(test_x_copy)), recall_score(test_y, clf.predict(test_x_copy)), precision_score(test_y, clf.predict(test_x_copy)), f1_score(test_y, clf.predict(test_x_copy))
                results[classifier][feature]["accuracy"].append(acc_all - acc)
                results[classifier][feature]["recall"].append(rec_all - rec)
                results[classifier][feature]["precision"].append(prec_all - prec)
                results[classifier][feature]["f1"].append(f1_all - f1)

 
    #Store results as json with caida and timestamp
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    with open(f'../results/{current_time}_importance_{benign_data_file}_{attack_data_file}_{time_frame}.json', 'w') as fp:
        json.dump(results, fp)



