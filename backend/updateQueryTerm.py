# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
import json
import config
import time

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

    payload = {'size': 10000}
    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=queryTypes)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    buckets = dataDict['aggregations']['total']['buckets']
    for bucket in buckets:
        print(bucket['key'],bucket['doc_count'])
    print('\n')

# GET DATA FOR EDIT

phrasesForReplace = [
    {'painting':['maliarstvo','Tafelbild (Flügelretabel)','maliarstvo insitné','tempera','Gemälde','obraz','Tafelbild','maliarstvo ľudové','enkaustika']},
    {'oil painting':['olej']},
    {'watercolor painting':['akvarel','akvarel koláž tuš','akvarel tempera','kvaš']},
    {'drawing':['kresba', 'Zeichnung','fix']},
    {'charcoal drawing':['uhel','rudka hnědá','rudka podkresba tužkou','sépie lavírovaná','rudka','coal drawing']},
    {'pencil drawing':['pastelka barevná','tužka','pastelka modrá','tužka černá']},
    {'pastel drawing':['pastel']},
    {'chalk drawing':['křída','křída barevná','křída barevná nesprašná','křídy barevné']},
    {'ink drawing':['tuš','rudka tuš běloba','lavírovaná tuš tempera','lavírovaná sépií tuš bistrem','kresba perem tuš','inkoust','perokresba lavírovaná']},
    {'graphic print':['monotyp','grafika','Grafika','Druck','počítačová grafika','rytina']},
    {'lithography':['litografie']},
    {'woodcut':['dřevoryt','xylografie']},
    {'book':['bibliofília a staré tlače']},
    {'new media':['intermédiá']},
    {'architecture':['architektúra']},
    {'photography':['fotografia','fotografie černobílá','dokumentárna fotografia','fotografie černobílá zvětšenina','Farbfoto','Fotogramm','fotografie digitální barevná pozitiv']},
    {'applied art':['úžitkové umenie','umelecké remeslo','kov','drevo']},
    {'sculpture':['sochárstvo','Büste','sochárstvo insitné','Skulptur','Plastik','Sitzstatue','perforace reliéf','Brunnenfigur','Denkmalmodell']},
    {'other':['koláž','mosaika','asambláž','interpretácia']}
]

for phrasesSet in phrasesForReplace:
    rightPhrase = list(phrasesSet.keys())[0]
    replaceList = []
    for wrongPhrase in phrasesSet[rightPhrase]:
        replaceList.append({"match_phrase": {searchedField: wrongPhrase}})

    ctxScript = "ctx._source."+searchedField+" = '"+ rightPhrase +"'"

    query = {
        "query": {
            "bool": {
                "should": replaceList
            }
        },
        "script": {
            "inline": ctxScript
        }
    }

    payload = {'size': 10000}
    rawData = requests.post('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_update_by_query',
                           auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    print(rightPhrase + ' - documents updated: '+str(dataDict["updated"]))

time.sleep(1)
print('\n')
print('Current items in '+searchedField+' :')
getTypesFromElastic()
