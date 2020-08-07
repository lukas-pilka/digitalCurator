# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config
import connector

searchedField = 'dating'


# GET CURRENT TYPES - searches all docs without field date_earliest and aggregates it by value
def getTypesFromElastic():
    queryTypes = {
        "query": {
            "bool": {
                "must_not": {
                    "exists": {
                        "field": "date_earliest"
                    }
                }
            }
        },
        "aggs": {
            "total": {
                "terms": {
                    "field": "dating.keyword",
                    "size": 100
                }
            }
        }
    }

    payload = {'size': 10000}
    rawData = requests.get(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=queryTypes)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)

    artworks = dataDict['hits']['hits'] # gets artworks from respond json
    for artwork in artworks:
        try: # If dating can be converted to integer then it is saved directly to date_earliest and date_latest (both same value)
            artwork['_source']['date_earliest'] = int(artwork['_source']['dating'])
            artwork['_source']['date_latest'] = int(artwork['_source']['dating'])
        except:
            pass
        harmfulWords = ['kolem', 'po', 'okolo', 'od', 'pred', 'um', 'vor', 'po roce', 'před', 'před rokem']  # add words for cut string after them
        for word in harmfulWords:
            try:
                if artwork['_source']['dating'].find(word) >= 0: # if any of harmful word is detected then proceed to cut it from dating
                    date = ''.join(list(artwork['_source']['dating'])[len(word)+1:]) # cut after harmful word + 1 for space
                    artwork['_source']['date_earliest'] = int(date) # if date is convertible into integer then it is saved to date earliest
                    artwork['_source']['date_latest'] = int(date) # same like date earliest
            except:
                pass

        # next try for dating conversion can be added here

        print(artwork)

        # WRITES NEW DATA

        if 'date_earliest' in artwork['_source']:
            documentData = {
                "doc": {'date_earliest': artwork['_source']['date_earliest'],
                        'date_latest': artwork['_source']['date_latest']},
                "doc_as_upsert": True
            }
            print('Updating data at ', artwork['_id'], documentData)
            connector.writeToElastic(artwork['_id'], documentData)  # saving data to Elastic

    # CURRENT RESULT

    buckets = dataDict['aggregations']['total']['buckets']
    for bucket in buckets:
        print(bucket['key'], bucket['doc_count'])

getTypesFromElastic()

