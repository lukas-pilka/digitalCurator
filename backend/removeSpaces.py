from connector import writeToElastic
import json
import config
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import os
import connector

# CONNECTION TO ELASTIC SEARCH
# Query returning artworks without detected objects
query = {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "must_not": {
              "exists": {
                "field": "detected_objects"
              }
            }
          }
        },
        {
          "bool": {
            "should": config.supportedWorkTypes
          }
        },
        {
          "bool": {
            "should": [
              {"term": {"is_free": True}}
            ]
          }
        }
      ]
    }
  }
}

payload = {'size': 10000}
rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                       auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)

import urllib.parse

for artwork in dataDict['hits']['hits']:
  if " " in artwork['_id']:
    oldId = artwork['_id']
    artwork['_id'] = oldId.replace(" ", "-")
    oldImageId = artwork['_source']['image_id']
    artwork['_source']['image_id'] = oldImageId.replace(" ", "-")

    # DOWNLODING IMAGE

    imagePath = 'temp/' + artwork['_id'] + '.jpg'
    iiUrl = 'storage.googleapis.com/tfcurator-artworks/artworks-all/'+oldId+'.jpg'
    repairedUrl = 'https://' + urllib.parse.quote(iiUrl)
    urllib.request.urlretrieve(repairedUrl, imagePath)

    connector.uploadToStorage('artworks-all/' + artwork['_source']['image_id'], 'temp/' + artwork['_source']['image_id'])  # saving image to google storage
    os.remove('temp/' + artwork['_source']['image_id'])  # deleting temporary image from local
    print(artwork['_source']['image_id'])

    documentData = {
      "doc": artwork,
      "doc_as_upsert": True
    }
    connector.writeToElastic(artwork['_id'], documentData)  # saving data to Elastic
    print(artwork['_id'])
    print(documentData)

    data = requests.delete(
      'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/item/' + oldId,
      auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic))
    print('Old Id Document Deleted')