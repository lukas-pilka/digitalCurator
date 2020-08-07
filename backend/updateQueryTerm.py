# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config
import connector

searchedField = 'work_type'

# GET CURRENT TYPES
def getTypesFromElastic():
    queryTypes = {
        "size":0,
        "aggs" : {
            "total" : {
                "terms" : {
                    "field" : searchedField+".keyword",
                    "size": 100
                }
            }
        }
    }

    payload = {'size': 1000}
    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=queryTypes)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    buckets = dataDict['aggregations']['total']['buckets']
    print('Field: ' + searchedField + '\n')
    for bucket in buckets:
        print(bucket['key'],bucket['doc_count'])
    print('\n')

getTypesFromElastic()

# GET DATA FOR EDITATION

valueForReplace = input('Value for replace: ')
newValue = input('New value: ')

query = {
    "query": {
        "match": {
            searchedField: valueForReplace
        }
    }
}

payload = {'size': 1000}
rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/test/_search',
                       auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)
artworks = dataDict['hits']['hits']

updatedCounter = 0
for artwork in artworks:
    if artwork['_source'][searchedField] == valueForReplace:
        artwork['_source'][searchedField] = newValue

        # WRITES NEW DATA

        documentData = {
            "doc": {searchedField: artwork['_source'][searchedField]},
            "doc_as_upsert": True
        }
        print('Updating data at ', artwork['_id'], documentData)
        connector.writeToElastic(artwork['_id'], documentData)  # saving data to Elastic
        updatedCounter += 1

print(str(updatedCounter) + ' documents updated')
print('Current items in '+searchedField+' :')

getTypesFromElastic()
