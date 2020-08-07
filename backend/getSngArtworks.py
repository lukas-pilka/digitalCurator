# IMPORTS

import os
import requests
from requests.auth import HTTPBasicAuth
import json
import config
from connector import writeToElastic




# WRITING TO THE STORAGE FUNCTION

def saveImage(key, imagePath):
    blob = bucket.blob(key)
    outfile = imagePath
    blob.upload_from_filename(outfile)


# START FOR SEARCH_AFTER

afterId = "SVK:VSG.G_2246"

# CONNECTION TO ELASTIC SEARCH

query = {
    "query": {
        "term": {
            "has_image": "true"
        }
    },
    "search_after": [afterId],
    "sort": [
        {"_id": "asc"}
    ]
}

payload = {'size': 10000}
rawData = requests.get('https://www.webumenia.sk/api/items_sk/_search',
                       auth=HTTPBasicAuth(config.userSngElastic, config.passSngElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)
artworks = dataDict['hits']['hits']

# ITERATING THROUGH ID LIST AND DOWNLOADING IMAGES

counter = 0
for item in artworks:

    dcId = 'WU-' + item['_id'].replace(":", "-").replace('.', '-').replace('_', '-')  # creating digital curator id from original Id
    item['_source']['original_id'] = item['_id'] # setting original_id as formal id
    del item['_source']['id']  # deleting formal id

    imageUrl = 'https://www.webumenia.sk/dielo/nahlad/' + item['_source']['original_id'] + '/800'  # creating image url from original id
    imageName = dcId + '.jpg'  # creating image file name from digital curator id
    img_data = requests.get(imageUrl).content  # downloading image
    with open('temp/' + imageName, 'wb') as handler:  # saving image to temp
        handler.write(img_data)
    saveImage('artworks-all/' + imageName, 'temp/' + imageName)  # uploading image to Storage bucket from temp
    os.remove('temp/' + imageName)  # deleting image from temp
    print('Downloaded image original ID ' + item['_source']['original_id'] + ', order ' + str(counter) + ' from url ' + imageUrl)

    documentData = {
        "doc": item['_source'],
        "doc_as_upsert": True
    }
    print('Artwork found: ', dcId, documentData)
    writeToElastic(dcId, documentData)

    counter += 1

print('Finished successfully')

