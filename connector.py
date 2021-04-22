# SETUP FOR GOOGLE STORAGE

import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

cred = credentials.Certificate("/Users/lukas/PycharmProjects/keys/digital-curator-a894b9b08c2b.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'digital-curator.appspot.com'
})


# SETUP FOR ELASTIC

import requests
from requests.auth import HTTPBasicAuth
import config

bucket = storage.bucket()

# WRITING TO THE STORAGE FUNCTION

def uploadToStorage(outputFile, originalFile):
    blob = bucket.blob(outputFile)
    outfile = originalFile
    blob.upload_from_filename(outfile)

# WRITE TO ELASTIC

def writeToElastic(documentId, documentData):

    payload = ''
    data = requests.post(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks3/_update/' + documentId,
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=documentData)
    print('Successfully posted to the Elastic Search database!')
