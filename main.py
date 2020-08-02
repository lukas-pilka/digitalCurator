# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config

# CONNECTION TO ELASTIC SEARCH

def callElastic(query):
    payload = ""
    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    return (dataDict)

# Query returning frequent object types

getObjectTypes = {
    "size":0,
    "aggs" : {
        "Total mediums" : {
            "terms" : {
                "field" : "objects.object.keyword",
                "size": 100
            }
        }
    }
}

objectTypes = callElastic(getObjectTypes)
print(objectTypes)
for object in objectTypes['aggregations']['Total mediums']['buckets']:
    print(object)

# Query for finding artworks containing selected object

searchedObject = "house"

getByObject = {
  "query": {
    "bool": {
      "must": [
        {"match": {"objects.object": searchedObject}}
        #{"match": {"objects.object": "Animal"}}
      ]
    }
  },
  "_source": {
    "includes": [
      "_id",
      "objects.object",
      "objects.score",
      "objects.boundBox",
    ]
  }
}


artworks = callElastic(getByObject)['hits']['hits']
print(str(len(artworks)) +' results')

# Preparing data for web

artworksForWeb = []

for artwork in artworks:
  imageUrl = 'https://storage.googleapis.com/digital-curator.appspot.com/artworks-all/' + artwork['_id'] + '.jpg'  # Creating img url from artwork id
  for object in artwork['_source']['objects']:
      object['score'] = round(object['score'], 2)
  artworksForWeb.append({'artworkDescription': artwork, 'artworkImage': imageUrl})

# flask

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def hello_world():
    return render_template('index.html',
                           artworksForWeb=artworksForWeb,
                           searchedObject=searchedObject
                           )