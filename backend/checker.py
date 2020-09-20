import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
import requests
from requests.auth import HTTPBasicAuth
import config
import json


# CONNECTING TO BUCKET
cred = credentials.Certificate("../../keys/digital-curator-a894b9b08c2b.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'digital-curator.appspot.com'
})
bucket = storage.bucket()
print("Bucket {} connected.".format(bucket.name))


# CONNECTION TO ELASTIC SEARCH
def load10kFromElastic(afterId):
    query = {
        "size":10000,
        "query": {
                "match_all": {}
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
    for request in range(20):
        print('Loading IDs...')
        if len(elasticIdsList) >= 1:
            load10kFromElastic(elasticIdsList[-1])
        else:
            load10kFromElastic('')
        print('IDs loaded: ' + str(len(elasticIdsList)) + ', Last one: ' + elasticIdsList[-1])


# COUNTING FILES ON GOOGLE STORAGE AND DELETING FILES WITHOUT ELASTIC RECORD
def filesChecker():
    print('counting Cloud Storage images...')
    trueCounter = 0
    falseCounter = 0
    prefix ='artworks-all'
    for artwork in bucket.list_blobs(prefix=prefix): # Checking Google Cloud Storage
        artworkFileName = artwork.name
        artworkIdStart = len(prefix) + 1
        artworkIdEnd = artworkFileName.find('.jpg')
        artworkId = ''.join(list(artworkFileName)[artworkIdStart:artworkIdEnd])  # cut all letters before xStart and after xEnd
        if artworkId in elasticIdsList:
            trueCounter += 1
            print(artworkFileName + ' has record in Elastic. '+ str(trueCounter) + ' with record in Elastic')
        else:
            print('!!! ' +artworkFileName + ' has NOT record in Elastic. ' + str(falseCounter) + ' without record in Elastic')
            blob = bucket.blob(artwork.name)
            blob.delete()
            print('Image deleted')
            falseCounter += 1

    print(str(trueCounter) + ' with record in Elastic: REMAINED')
    print(str(falseCounter) + ' without record in Elastic: DELETED')


# COUNTING FILES ON GOOGLE STORAGE
def filesCounter():
    print('counting Cloud Storage images...')
    counter = 0
    for artwork in bucket.list_blobs(prefix='artworks-all'): # Checking Google Cloud Storage
        counter += 1
    print(str(counter) + ' files on Google Cloud Storage')


elasticIdsList = []
# loadAllFromElastic()
filesCounter()



