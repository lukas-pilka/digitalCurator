# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config
import connector

# EXTRACT DATE RANGE FROM DATING AT SINGLE ARTWORK
# If dating can be decoded, it extends input dict by adding date_earliest and date_latest
# It returns extended dict

def setDateRange(artwork):
    if 'dating' in artwork.keys():
        # if unknown mention in dating
        unknownWords = [None, '', 'neurčena', 'neurčeno', 'neurčen', 'neznámý', 'nedatováno', 'nedatované', 'undatiert', 'Undatiert', 'undated']  # add words for cut string after them
        for word in unknownWords:  # if unknown word in dating, script tries to cut it and convert dating to integer
            if artwork['dating'] == word:
                artwork['dating'] = 'unknown'

        # replaces specific values
        wordPairs = [
            ['15. Jahrhundert (?)', [1400, 1500]],
            ['16. Jahrhundert', [1500, 1600]],
            ['16. století', [1500, 1600]],
            ['16. Jh.', [1500, 1600]],
            ['Mitte 16. Jahrhundert', [1540,1560]],
            ['2. Hälfte 16. Jahrhundert',[1550,1600]],
            ['17. století', [1600, 1700]],
            ['17. Jhdt.', [1600, 1700]],
            ['17. Jh.', [1600, 1700]],
            ['17. Jahrhundert', [1600, 1700]],
            ['1. Hälfte 17. Jahrhundert', [1600, 1650]],
            ['2. Hälfte 17. Jahrhundert', [1650, 1700]],
            ['Mitte 17. Jahrhundert',[1640,1660]],
            ['Ende 17. Jh.', [1680, 1700]],
            ['18. století', [1700, 1800]],
            ['18. Jh.', [1700, 1800]],
            ['18. Jahrhundert', [1700, 1800]],
            ['pol. 18. stol',[1740,1760]],
            ['1740 - 1745?',[1740,1745]],
            ['2. pol. 18. stol',[1750,1800]],
            ['2. Hälfte 18. Jahrhundert', [1750, 1800]],
            ['2. Hälfte 18., Beginn 19. Jahrhundert', [1750, 1810]],
            ['Ende 18., Beginn 19. Jahrhundert', [1790,1810]],
            ['19. století', [1800, 1900]],
            ['19. Jahrhundert', [1800, 1900]],
            ['Anfang 19. Jahrhundert', [1800,1810]],
            ['1. Hälfte 19. Jahrhundert', [1800,1850]],
            ['2. Hälfte 19. Jahrhundert', [1850, 1900]],
            ['90. léta 19. století', [1890, 1900]],
            ['Prelom 18. a 19. storočia', [1790, 1810]],
            ['20. století', [1900, 2000]]
        ]
        for wordPair in wordPairs:
            try:
                if artwork['_source']['dating'] == wordPair[0]:
                    artwork['_source']['date_earliest'] = wordPair[1][0]
                    artwork['_source']['date_latest'] = wordPair[1][1]
            except:
                pass

        # if harmful words in dating, script tries to cut it
        harmfulPrepositions = ['kolem ', 'po ', 'okolo ','cca ', 'od ', 'do ', 'asi ', 'mezi ', 'pred ','kol. ' , 'Kolem ', 'gegen ', 'um ','Um ', 'vor ', 'po roce ', 'před ', 'před rokem ', 'kolem roku ', 'nach ', 'wohl ', 'wohl vor ', 'zwischen ', 'around ', 'before ', 'about ', 'dated ', 'ca. ', 'Ca. ', 'after ', 'circa ','active ','c. ', 'y after ']  # add words for cut string after them (including space)
        harmfulSupplements = [' datiert',' (?)',]  # add words for cut string after them (including space)
        if 'date_earliest' not in artwork.keys(): # if previous attempts to set date_earliest was successful it skips this part
            for word in harmfulPrepositions:
                if artwork['dating'].find(word) >= 0:  # if any of harmful word is detected then proceed to cut it from dating
                    artwork['dating'] = ''.join(list(artwork['dating'])[len(word):])  # cut after harmful word
            for word in harmfulSupplements:
                if artwork['dating'].find(word) >= 0:  # if any of harmful word is detected then proceed to cut it from dating
                    wordStart = artwork['dating'].find(word)
                    artwork['dating'] = ''.join(list(artwork['dating'])[:wordStart])  # cut before harmful word

        # if dating can be converted to integer then it is saved directly to date_earliest and date_latest (both same value)
        try:
            artwork['date_earliest'] = int(artwork['dating'])
            artwork['date_latest'] = int(artwork['dating'])
        except:
            pass

        # if junction in dating
        separators = [' - ','-','–','—',' − ','/','und']
        if 'date_earliest' not in artwork.keys(): #if previous attempts to set date_earliest was successful it skips this part
            for separator in separators:
                if separator in artwork['dating']:
                    try:
                        dateEarliestEnd = artwork['dating'].find(separator)   # searches for separator for finding the end of dateEarliest
                        artwork['date_earliest'] = artwork['dating'][:dateEarliestEnd]  # cut all letters after dateEarliestEnd
                        artwork['date_earliest'] = int(artwork['date_earliest']) # converting to integer

                        dateLatestStart = artwork['dating'].find(separator)  # searches for ' - ' for finding the end of dateEarliest
                        artwork['date_latest'] = artwork['dating'][dateLatestStart+len(separator):]  # cut all letters before dateLatestEnd
                        artwork['date_latest'] = int(artwork['date_latest'])  # converting to integer
                    except:
                        pass

        # printing result
        if 'date_earliest' in artwork.keys() and 'date_latest' in artwork.keys():
            print('Dating decoded, set up date_earliest: ' + str(artwork['date_earliest']) + ', date_latest: ' + str(artwork['date_latest']) + ' from dating ' + artwork['dating'])
        else:
            print("Unknown dating, can't decode : " + artwork['dating'])

    else:
        print('No dating in the dictionary, it is not possible to extract dates')

    return artwork

# CHECK RECORDED ARTWORKS WITHOUT DATE RANGE AND TRY TO SET DATE RANGE
def checkRecordedArtworks():
    queryTypes = {
        "query": {
            "bool": {
                "must": {
                    "exists": {"field": "dating"}
                },
                "must_not": [
                    {"exists": {"field": "date_earliest"}},
                    {"term": {"dating": "unknown"}},
                    {"term": {"dating": ""}}
              ]
            }
        }
    }

    payload = {'size': 10000}
    rawData = requests.get(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=queryTypes)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    rawArtworks = dataDict['hits']['hits'] # gets artworks list from respond json
    artworks = [x['_source'] for x in rawArtworks] # extract _source part from items
    for i in range(len(rawArtworks)):
        artworks[i]['id'] = rawArtworks[i]['_id'] # temporary adds id to artwork dict. It will be removed bellow

    # Iterating threw artworks from elastic and calling setDateRange function
    counter = 0
    for artwork in artworks:
        counter += 1
        print(str(counter) + ' Exploring : ' + str(artwork))
        setDateRange(artwork)
        if 'date_earliest' and 'date_latest' in artwork:
            dcId = artwork['id']  # Taking id from dic. WritetoElastic sends id separately
            artwork.pop('id') # Removing id from dict (It was added in gaetting dates from Elastic)
            documentData = {
                "doc": artwork,
                "doc_as_upsert": True
            }
            connector.writeToElastic(dcId, documentData)  # saving data to Elastic

# RUN IF YOU WANT CHECK RECORDED ARTWORKS WITHOUT DATE RANGE
# checkRecordedArtworks()



