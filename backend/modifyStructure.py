from connector import writeToElastic
import json
import config
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# CONNECTION TO ELASTIC SEARCH
lastTimeSwitch = input('Select artworks by previous object update. Set time in format 2000-01-01T23:59:00Z:') or '2022-01-01T23:59:00Z'
print('Connecting to Elastic Search...')
# Query returning artworks without detected objects
query = {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "should": [
                {"bool": {"must_not": {"exists": {"field": "detected_objects_updated"}}}},
                {"range": {"detected_objects_updated": {"gte": lastTimeSwitch}}}
            ]
          }
        },
        {
          "bool": {
            "should": [
              {"term": {"work_type": "graphic"}},
              {"term": {"work_type": "painting"}},
              {"term": {"work_type": "drawing"}}
            ]
          }
        }
      ]
    }
  }
}

payload = {'size': 10000}
rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks3/_search',
                       auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)

counter = 0
for artwork in dataDict['hits']['hits']:
    counter += 1
    now = datetime.now()
    now = now.strftime("%Y-%m-%dT%H:%M:%SZ")  # preparing time in elastic format
    documentId = artwork['_id']
    artwork['_source']['title'] = 'ahoj'
    oldDetectedObjects = artwork['_source']['detected_objects']
    newDetectedObjects = []
    for oldObject in oldDetectedObjects:
        objectName = oldObject['object']
        objectScore = oldObject['score']
        boundBox  = oldObject['boundBox']
        newObject = {objectName:{'score':objectScore,'boundBox':boundBox}}
        newDetectedObjects.append(newObject)

    artwork['_source']['detected_objects'] = newDetectedObjects

    documentData = {
        "doc": {
            'detected_objects': newDetectedObjects,
            "detected_objects_updated": now,
        },
        "doc_as_upsert": "true"
    }
    print(counter)
    print(documentId)
    print(documentData)
    writeToElastic(documentId, documentData)
