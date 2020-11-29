import pyparsing as pp
import pymongo
import nltk
import re
import string
from pymongo import MongoClient
from flask import Flask, render_template, request, url_for
from collections import Counter

application = app = Flask(__name__)
cluster = MongoClient("mongodb+srv://dbUser:CQrPZIykkXRAbJDA@cluster0.vairi.mongodb.net/texts?retryWrites=true&w=majority")
db = cluster["texts"]
collection = db["texts"]

# Variables
textDictionary = dict()
dictionaryForDB = dict()
searchableWord = ""
readContent = ""
frequencyOfSearchableWord = 0
frequencyOfPhrases = 0
isPhrase = False


@app.route('/', methods = ['POST', 'GET'])
def index():

    # Getting variables
    global textDictionary
    global searchableWord
    global frequencyOfSearchableWord
    global isPhrase
    global readContent

    # Writing data to the DB
    if(collection.count() == 0):
        searchForWords()
        makeDictionaryForDB()

    # Getting form's values
    processSearchButton = request.form.get('processSearch')
    processSearchMostUsedWordsButton = request.form.get('processSearchingWords')

    if request.method == 'POST':

        # Handling button clicks
        if processSearchButton == "Порахувати вживаність":
            searchableWord = request.form['searchableWord']
            if containsMultipleWords(searchableWord):
                isPhrase = True
                if collection.count() != 0:
                    sudoRead()
                isPhraseIn(searchableWord, readContent)

            else:
                isPhrase = False
                frequencyOfSearchableWord = searchForWordInDB(searchableWord)[1]
                
            return render_template('index.html', count = frequencyOfSearchableWord, word = searchableWord , isPhrase = isPhrase, phraseCount = frequencyOfPhrases)

        elif processSearchMostUsedWordsButton == "Знайти найбільш вживані слова":
            topDict = findMostUsedWords()
            return render_template('index.html', mostUsedWords = topDict)
        else:
            return render_template('index.html')


def searchForWordInDB(str):
    documents = collection.find()
    word = str
    count = 0
    if collection.find( { str : { str: "$regex" } } ):
        for key, value in documents.next().items():
            documentValue = value
            documentKey = key
            if documentKey == str:
                it = iter(documentValue.values())
                word = next(it)
                count = next(it)

    return word, count

def makeDictionaryForDB():
    for key, value in textDictionary.items():
        dictionaryForDB[key] = {
            "word": key,
            "count": value
        }

    collection.insert_one(dictionaryForDB)


def containsMultipleWords(s):
    return len(s.split()) > 1

def searchForWords():
    global textDictionary
    global readContent


    for item in range(1,42):
        with open("./texts/" + str(item) + ".txt", "r", encoding="utf-8") as f:
            readContent = readContent + " " + f.read()

    textDictionary = splitPlaintText(readContent)

def sudoRead():
    global readContent

    for item in range(1,42):
        with open("./texts/" + str(item) + ".txt", "r", encoding="utf-8") as f:
            readContent = readContent + " " + f.read()

def splitPlaintText(str):
    preResult = createDictionary(str)
    print(preResult)
    result = deleteSecondaryWords(preResult)
    return result


def createDictionary(str):
    counts = dict()
    tokens = nltk.word_tokenize(str.lower())
    for word in tokens:
        if word not in counts.keys():
            counts[word] = 0
        counts[word] = counts[word] + 1

    endDictionary = dict()
    for k,v in sorted(counts.items(), key=lambda words: words[1], reverse=True):
        endDictionary[k] = v

    return endDictionary


def deleteSecondaryWords(dict):
    del dict['і']
    del dict['в']
    del dict['у']
    del dict['не']
    del dict['що']
    del dict['на']
    del dict['до']
    del dict['нас']
    del dict['–']
    del dict['а']
    del dict['він']
    del dict['є']
    del dict['з']
    del dict['як']
    del dict['я']
    del dict['це']
    del dict['ми']
    del dict['його']
    del dict['про']
    del dict['хто']
    del dict['коли']
    del dict['за']
    del dict['нам'] 
    del dict['’']
    del dict['!']
    del dict[',']
    del dict['»']
    del dict['«']
    del dict[':']
    del dict['та']
    del dict['які']
    del dict['для']
    del dict['те']
    del dict['щоб']
    del dict['того']
    del dict['її']
    del dict['але']
    del dict['бо']
    del dict['той']
    del dict['?']
    del dict['який']
    del dict['яка']
    del dict['ті']

    return dict

def findMostUsedWords():
    top = 0
    topList = []
    documents = collection.find()
    for item in documents.next().items():
        if top < 4:
            topList.append(item)
            top += 1
        else:
            break
    topList.pop(0)

    topDictionary = dict()
    topDictionary[topList[0][1]['word']] = topList[0][1]['count']
    topDictionary[topList[1][1]['word']] = topList[1][1]['count']
    topDictionary[topList[2][1]['word']] = topList[2][1]['count']

    return topDictionary

def isPhraseIn(phrase, text):
    global frequencyOfPhrases
    phrase = phrase.lower()
    text = text.lower()

    rule = pp.ZeroOrMore(pp.Keyword(phrase))
    for t in rule.scanString(text):
        if t:
            frequencyOfPhrases += 1


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080,debug=False)