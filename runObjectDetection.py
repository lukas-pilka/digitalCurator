from writeToElastic import writeToElastic
from tfObjectDetection import tfObjectDetection
import json
import config
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import os
from PIL import Image

# CONNECTION TO ELASTIC SEARCH
# Query returning artworks without detected objects
query = {
  "query": {
    "bool": {
      "must_not": {
        "exists": {
          "field": "objects"
        }
      }
    }
  }
}

payload = {'size': 10000}
rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                       auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)
artworks = dataDict['hits']['hits']
print(str(len(artworks))+' artworks for object detection.')

# Iterating through artworks list

for artwork in artworks:
    imageUrl = 'https://storage.googleapis.com/digital-curator.appspot.com/artworks-all/'+artwork['_id']+'.jpg' # Creating img url from artwork id
    imageFileName = 'temp/'+artwork['_id']+'.jpg' # Creating image file name from artwork id
    urllib.request.urlretrieve(imageUrl, imageFileName) # Downloading image from url and saving to file name
    image = Image.open(imageFileName)  # Converting to PIL image file
    print(image)
    # Preparing json for upload and calling Tensor Flow object detection
    documentData = {
        "doc": {
            "objects": tfObjectDetection(image),
        },
        "doc_as_upsert": True
    }
    print('Detected objects: ' + str(documentData))
    writeToElastic(artwork['_id'], documentData) # Writing to Digital Curator Elastic Search DB
    print('Data recorded for: ' + imageUrl)
    os.remove(imageFileName) # Removing image
