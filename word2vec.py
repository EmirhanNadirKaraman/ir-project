import gensim.downloader as api
import numpy as np

model = api.load('word2vec-google-news-300')

def get_vector(word_list: list[str]):
    lst = []
    for word in word_list:
        if word in model:
            lst.append(model[word])

    return np.mean(lst, axis=0) if lst else np.zeros(300)
