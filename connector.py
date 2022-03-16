# SETUP FOR GOOGLE STORAGE

import firebase_admin
import config
from firebase_admin import credentials
from firebase_admin import storage

try:

    cred = credentials.Certificate(config.googleCredentialsKey)
except:
    cred = credentials.Certificate('../'+config.googleCredentialsKey)

firebase_admin.initialize_app(cred, {
    'storageBucket': 'tfcurator-artworks'
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
