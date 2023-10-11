import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score
from sklearn.base import clone
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier


def classifier_name(clf):
    return clf.__class__.__name__

classifier_list = [ 
    RandomForestClassifier(n_estimators=10, max_depth=2),
    SVC(kernel='linear', C=1),
    DecisionTreeClassifier(max_depth=10),
    MLPClassifier(hidden_layer_sizes=(20, 20, 20), max_iter=1000, alpha=0.01),
    ]

results = {
}

#Generate random data frame with 1000 rows and 13 columns
data = pd.DataFrame(np.random.randint(10, size=(1000, 14)))
#train classifiert with data frame
for classifier in classifier_list:
    results[classifier_name(classifier)] = []
    classifier.fit(data, data[13])


for run in range(100):
    #classify the data frame and measure the time
    for classifier in classifier_list:
        start = time.time()
        result = classifier.predict(data)
        end = time.time()
        results[classifier_name(classifier)].append(end - start)

import json
import datetime
#Store results as json with caida and timestamp
current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
with open(f'./{current_time}_classification_duration.json', 'w') as fp:
    json.dump(results, fp)
