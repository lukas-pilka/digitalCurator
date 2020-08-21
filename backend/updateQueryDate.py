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
                "must_not": [
                {"exists": {"field": "date_earliest"}},
                {"term": {"dating": "unknown"}}
              ]
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
    print(len(artworks))
    for artwork in artworks:

        # if unknown mention in dating
        unknownWords = [None, '', 'neurčena', 'neurčeno', 'neurčen', 'neznámý', 'nedatováno', 'nedatované', 'undatiert','Undatiert']  # add words for cut string after them
        for word in unknownWords:  # if unknown word in dating, script tries to cut it and convert dating to integer
            try:
                if artwork['_source']['dating'] == word:
                    artwork['_source']['dating'] = 'unknown'
            except:
                pass

        # replaces specific values
        wordPairs = [
            ['16. století',[1500,1600]],
            ['17. století', [1600, 1700]],
            ['18. století', [1700, 1800]],
            ['19. století', [1800, 1900]],
            ['90. léta 19. století', [1890,1900]],
            ['Prelom 18. a 19. storočia', [1790, 1810]],
            ['16. Jahrhundert', [1500, 1600]],
            ['17. Jahrhundert', [1600, 1700]],
            ['18. Jahrhundert', [1700, 1800]],
            ['19. Jahrhundert', [1800, 1900]],
            ['15. Jahrhundert (?)', [1400, 1500]],
            ['um 1445/1450', [1445, 1450]],
            ['um 1470/1480', [1470, 1480]],
            ['um 1485/1490', [1485, 1490]],
            ['um 1490/1491', [1490, 1491]],
            ['um 1485/1490', [1485, 1490]],
            ['um 1510/1520', [1510, 1520]],
            ['um 1760/1800', [1750, 1800]],
            ['um 1770/1780', [1770, 1780]],
            ['um 1820/1855', [1820, 1855]]
        ]

        for wordPair in wordPairs:
            try:
                if artwork['_source']['dating'] == wordPair[0]:
                    artwork['_source']['date_earliest'] = wordPair[1][0]
                    artwork['_source']['date_latest'] = wordPair[1][1]
            except:
                pass

        # If dating can be converted to integer then it is saved directly to date_earliest and date_latest (both same value)
        try:
            artwork['_source']['date_earliest'] = int(artwork['_source']['dating'])
            artwork['_source']['date_latest'] = int(artwork['_source']['dating'])
        except:
            pass

        # if harmful word in dating, script tries to cut it and convert dating to integer
        harmfulWords = ['kolem', 'po', 'okolo', 'od', 'pred', 'um', 'vor', 'po roce', 'před', 'před rokem','kolem roku', 'nach', 'wohl', 'wohl vor']  # add words for cut string after them
        for word in harmfulWords:
            try:
                if artwork['_source']['dating'].find(word) >= 0: # if any of harmful word is detected then proceed to cut it from dating
                    date = ''.join(list(artwork['_source']['dating'])[len(word)+1:]) # cut after harmful word + 1 for space
                    artwork['_source']['date_earliest'] = int(date) # if date is convertible into integer then it is saved to date earliest
                    artwork['_source']['date_latest'] = int(date) # same like date earliest
            except:
                pass
        # if dash in dating
        separators = [' - ','-','–','/']
        for separator in separators:
            try:
                if separator in artwork['_source']['dating']:

                    dateEarliestEnd = artwork['_source']['dating'].find(separator)   # searches for separator for finding the end of dateEarliest
                    artwork['_source']['date_earliest'] = ''.join(list(artwork['_source']['dating'])[:dateEarliestEnd])  # cut all letters after dateEarliestEnd
                    artwork['_source']['date_earliest'] = int(artwork['_source']['date_earliest']) # converting to integer

                    dateLatestStart = artwork['_source']['dating'].find(separator)  # searches for ' - ' for finding the end of dateEarliest
                    artwork['_source']['date_latest'] = ''.join(list(artwork['_source']['dating'])[dateLatestStart+len(separator):])  # cut all letters before dateLatestEnd
                    artwork['_source']['date_latest'] = int(artwork['_source']['date_latest'])  # converting to integer

            except:
                pass

        # next try for dating conversion can be added here

        # WRITES NEW DATA

        if 'date_earliest' and 'date_latest' in artwork['_source']:
            documentData = {
                "doc": {'date_earliest': artwork['_source']['date_earliest'],
                        'date_latest': artwork['_source']['date_latest'],
                        'dating': artwork['_source']['dating']
                        },
                "doc_as_upsert": True
            }
            print(documentData)
            connector.writeToElastic(artwork['_id'], documentData)  # saving data to Elastic
        elif 'dating' in artwork['_source']:
            documentData = {
                "doc": {
                        'dating': artwork['_source']['dating']
                        },
                "doc_as_upsert": True
            }
            print(documentData)
            connector.writeToElastic(artwork['_id'], documentData)  # saving data to Elastic
        else:
            pass

    # CURRENT RESULT

    buckets = dataDict['aggregations']['total']['buckets']
    for bucket in buckets:
        print(bucket['key'], bucket['doc_count'])

getTypesFromElastic()

