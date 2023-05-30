import numpy as np
import json 


from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from word2vec import *
import math 

no_of_bins = 20

thumbnail_objects = [
    {
        "label": "Accessories",
        "confidence": 0.9999958038330078
    }
]

videos = {}
with open('videos.json', 'r') as f: 
    videos = json.load(f)

x = []
y = []

for video in videos.values():
    print(type(video), video)

    description = video["video"]["description"].split() or []
    tags = video["video"].get('tags', []) or []
    labels = [inner["label"] for inner in video["video"]["thumbnail_objects"]] or []

    words = description + tags + labels
    x.append(get_vector(words))

    view = video['video']['view_count']
    sub_count = video['channel']['subscriber_count']

    y.append(math.tanh(math.log(view) / math.log(sub_count)) * no_of_bins)


print(x[0])
print(y[0])

# Assuming you have your features in X and labels in y
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

# Scale the input data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

mlp = MLPClassifier(hidden_layer_sizes=(100, 50), activation='relu', solver='adam', max_iter=500)
mlp.fit(X_train_scaled, y_train)

accuracy = mlp.score(X_test_scaled, y_test)

print(accuracy)


