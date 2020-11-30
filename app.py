#! /usr/bin/env python
# -*- coding: utf-8 -*-


# What is used for this app:
# - Flask framework
# - MongoDB (pymongo module)
# - Natural Language ToolKit
# - PyParsing
# - Amazon Web Services


# Imports
from flask import Flask, render_template, request, url_for
from pymongo import MongoClient
import pyparsing as pp
import pymongo          
import os, sys
import string
import nltk

# Flask
application = app = Flask(__name__)

# Database
cluster = MongoClient("mongodb+srv://dbUser:CQrPZIykkXRAbJDA@cluster0.vairi.mongodb.net/texts?retryWrites=true&w=majority")
db = cluster["texts"]
collection = db["texts"]

# Paths
root = os.path.dirname(os.path.abspath(__file__))
texts_path = root + "/texts/"


# Variables
textDictionary = dict()
dictionaryForDB = dict()
searchableWordFormInput = ""
searchableWord = ""
readContent = ""
frequencyOfSearchableWord = 0
frequencyOfPhrases = 0
isPhrase = False




# Methods
@app.route('/', methods = ['POST', 'GET'])
def index():

    # Getting variables
    global textDictionary
    global searchableWordFormInput
    global searchableWord
    global frequencyOfSearchableWord
    global isPhrase
    global readContent


    # Getting form's values
    processSearchButton = request.form.get('processSearch')
    processSearchMostUsedWordsButton = request.form.get('processSearchingWords')

    if request.method == 'POST':

        # Handling button clicks
        if processSearchButton == "Порахувати вживаність":
            searchableWordFormInput = request.form['searchableWord']

            searchableWord = searchableWordFormInput.lstrip()

            if containsMultipleWords(searchableWord):
                isPhrase = True
                if collection.estimated_document_count() != 0:
                    sudoRead()
                isPhraseIn(searchableWord, readContent)

            else:
                isPhrase = False
                frequencyOfSearchableWord = searchForWordInDB()[1]
                
            return render_template('index.html', count = frequencyOfSearchableWord, word = searchableWord , isPhrase = isPhrase, phraseCount = frequencyOfPhrases)

        elif processSearchMostUsedWordsButton == "Знайти найбільш вживані слова":
            topDict = findMostUsedWords()
            return render_template('index.html', mostUsedWords = topDict)
        else:
            return render_template('index.html')
    else:
        return render_template('index.html')

def searchForWordInDB():
    word = searchableWord
    count = 0
    

    documents = list(collection.find({ "word": word }))
    if len(documents) != 0:
        word = documents[0]['word']
        count = documents[0]['count']

        return word, count
    else:
        return word, count
    

def makeDictionaryForDB():
    for key, value in textDictionary.items():
        dictionaryForDB = {
            "word": key,
            "count": value
        }
        collection.insert_one(dictionaryForDB)


def containsMultipleWords(s):
    return len(s.split()) > 1

def searchForWords():
    global textDictionary
    global readContent

    dirs = os.listdir(texts_path)

    for item in dirs:
        with open(texts_path + item, encoding="utf8") as f:
            if os.path.isfile(texts_path + item):
                readContent = readContent + " " + f.read()

    textDictionary = splitPlaintText(readContent)

def sudoRead():
    global readContent

    dirs = os.listdir(texts_path)

    for item in dirs:
        with open(texts_path + item, encoding="utf8") as f:
            if os.path.isfile(texts_path + item):
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
    secondaryWords = ['і' , 'в', 'у', 'не', 'що', 'на', 'до', 'нас', '–', 'а', 'він', 'є', 'з', 'як', 'я', 'це', 'ми', 'його', 'про',
                    'хто', 'коли', 'за', 'нам', '’', '!', ',', '»', '«', ':', 'та', 'які', 'для', 'те', 'щоб', 'того', 'її', 'але', 'бо',
                    'той', '?', 'який', 'яка', 'ті', 'від']
    for item in secondaryWords:
        del some_dictionary[item]

    return some_dictionary

def findMostUsedWords():
    howMuchToFind = 3
    topList = []
    topDictionary = dict()
   
    topList = list(collection.find(sort=[("count", -1)]).limit(howMuchToFind))
    
    for list_item in range(3):
        topDictionary[topList[list_item]['word']] = topList[list_item]['count']

    return topDictionary

def isPhraseIn(phrase, text):
    global frequencyOfPhrases
    phrase = phrase.lower()
    text = text.lower()

    rule = pp.ZeroOrMore(pp.Keyword(phrase))
    for t, e, s in rule.scanString(text):
        if t:
            frequencyOfPhrases += 1


if __name__ == "__main__":
    # Writing data to the DB
    if(collection.estimated_document_count() == 0):
        searchForWords()
        makeDictionaryForDB()

    app.run(host="0.0.0.0", port=8080)