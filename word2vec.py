import gensim.downloader as api

model = api.load('word2vec-google-news-300')
print("model loaded")

for word in "These guys are hjlnsdfjgnvö in the world".split():
    if word in model:
        print(word, "is in the model")
    else:
        print(word, "is not in the model")
        print("*" * 100, "\n" * 10)
    print(model[word])
