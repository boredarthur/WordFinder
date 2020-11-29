#! /usr/bin/env python
# -*- coding: utf-8 -*-


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
    else:
        return render_template('index.html')

def searchForWordInDB(some_string):
    documents = collection.find()
    word = some_string
    count = 0
    if collection.find( { some_string : { some_string: "$regex" } } ):
        for key, value in documents.next().items():
            documentValue = value
            documentKey = key
            if documentKey == some_string:
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

def splitPlaintText(some_string):
    preResult = createDictionary(some_string)
    result = deleteSecondaryWords(preResult)
    return result


def createDictionary(some_string):
    counts = dict()
    tokens = nltk.word_tokenize(some_string.lower())
    for word in tokens:
        if word not in counts.keys():
            counts[word] = 0
        counts[word] = counts[word] + 1

    endDictionary = dict()
    for k,v in sorted(counts.items(), key=lambda words: words[1], reverse=True):
        endDictionary[k] = v

    return endDictionary


def deleteSecondaryWords(some_dictionary):
    secondaryWords = ['і' , 'в', 'у', 'не', 'що', 'на', 'до', 'нас', '-', 'а', 'він', 'є', 'з', 'як', 'я', 'це', 'ми', 'його', 'про',
                    'хто', 'коли', 'за', 'нам', '’', '!', ',', '»', '«', ':', 'та', 'які', 'для', 'те', 'щоб', 'того', 'її', 'але', 'бо',
                    'той', '?', 'який', 'яка', 'ті']
    for item in secondaryWords:
        del some_dictionary[item]

    return some_dictionary

def findMostUsedWords():
    top = 0
    howMuchToFind = 3
    topList = []
    documents = collection.find()
    for item in documents.next().items():
        if top < (howMuchToFind + 1):       # Takes also first document 'objectID'
            topList.append(item)
            top += 1
        else:
            break  
    topList.pop(0)  # Removes 'objectID'

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
    app.run(host='0.0.0.0', port=80, debug=False)