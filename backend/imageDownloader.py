import firebase_admin
from firebase_admin import credentials
from google.cloud import storage
import requests
from requests.auth import HTTPBasicAuth
import config
import json

# CONNECTION TO ELASTIC SEARCH
def load10kFromElastic(afterId):
    query = {
        "size":350,
        "query": {
        "bool": {
            "must": [
                {
                    "range": {
                        "date_earliest": {
                            "gte": 1775,
                            "lt": 1800
                        }
                    }
                },
                {
                    "match_phrase": {"detected_objects.object": "Person"}
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
    },
        "search_after": [afterId],
        "sort": [
            {"_id": "asc"}
        ]
    }

    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    artworks = dataDict['hits']['hits']
    for artwork in artworks:
        elasticIdsList.append(artwork['_id'])

def loadAllFromElastic():
    for request in range(1):
        print('Loading IDs...')
        if len(elasticIdsList) >= 1:
            load10kFromElastic(elasticIdsList[-1])
        else:
            load10kFromElastic('')
        print('IDs loaded: ' + str(len(elasticIdsList)) + ', Last one: ' + elasticIdsList[-1])

# CONNECTING TO BUCKET
def download_blob(source_blob_name, destination_file_name):

    storage_client = storage.Client.from_service_account_json('../../keys/tfcurator-c227c8fe0180.json')
    bucket = storage_client.bucket('tfcurator-artworks')
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Blob {} downloaded to {}.".format(
            source_blob_name, destination_file_name
        )
    )

elasticIdsList = []
loadAllFromElastic()
counter = 0
for id in elasticIdsList:
    sourceFileName = 'artworks-all/'+id+'.jpg'
    destinationFileName = 'before1800/'+id+'.jpg'
    download_blob(sourceFileName,destinationFileName)
    counter += 1
    print(counter)