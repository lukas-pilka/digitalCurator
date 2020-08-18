# IMPORTS

import requests
from requests.auth import HTTPBasicAuth
from random import randrange
import json
import config


# CONNECTION TO ELASTIC SEARCH

def callElastic(query):
    payload = ""
    rawData = requests.get(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    return (dataDict)


# Query returning frequent object types

getObjectTypes = {
    "size": 0,
    "aggs": {
        "Total mediums": {
            "terms": {
                "field": "detected_objects.object.keyword",
                "size": 10000
            }
        }
    }
}

objectTypesDict = callElastic(getObjectTypes)
objectTypes = []

# Selecting object types with more than 10 presences
for object in objectTypesDict['aggregations']['Total mediums']['buckets']:
    if object['doc_count'] >= config.minObjectsLimit:
        objectTypes.append(object['key'])

def getArtworksByObject(searchedObject):
    # Query for finding artworks containing selected object

    getByObject = {
        "size": 10000,
        "query": {
            "bool": {
                "must": [
                    {"match": {"detected_objects.object": searchedObject}}
                    ,
                    {
                        "bool": {
                            "must": [
                                {"exists": {"field": "detected_objects"}},
                                {
                                    "bool": {
                                        "should": [
                                            {"term": {"work_type": "graphic"}},
                                            {"term": {"work_type": "painting"}},
                                            {"term": {"work_type": "drawing"}}
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "_source": {
            "includes": [
                "_id",
                "detected_objects.object",
                "detected_objects.score",
                "detected_objects.boundBox",
                "title",
                "author",
                "gallery",
                "gallery",
                "date_earliest",
                "date_latest"
            ]
        }
    }

    artworks = callElastic(getByObject)['hits']['hits']
    print(str(len(artworks)) + ' results')

    # expanding data by imageUrl and topObjectScore

    expandedArtworks = []
    earliestWork = 10000
    latestWork = -10000

    for artwork in artworks:
        # generates image url
        imageUrl = 'https://storage.googleapis.com/digital-curator.appspot.com/artworks-all/' + artwork[
            '_id'] + '.jpg'  # Creating img url from artwork id
        artwork['_source']['image_url'] = imageUrl
        # rounds object score
        for object in artwork['_source']['detected_objects']:
            object['score'] = round(object['score'], 2)
        # selects searched object with highest score on image and saves it to topObjectScore (It's useful for sorting)
        topObjectScore = 0
        for objectSet in artwork['_source']['detected_objects']:
            if objectSet['object'] == searchedObject and objectSet['score'] >= topObjectScore:
                topObjectScore = objectSet['score']
        artwork['_source']['top_object_score'] = topObjectScore
        expandedArtworks.append(artwork)
    return expandedArtworks


# sorts expandedArtworks by topObjectScore

def sorter(artwork):
    score = artwork['_source']['top_object_score']
    return (score)


# get collection sum

getCollectionsSum = {
    "query": {
        "bool": {
            "must": {
                "exists": {
                    "field": "detected_objects"
                }
            }
        }
    },
    "size": 0,
    "aggs": {
        "galleries_sum": {
            "terms": {
                "field": "gallery.keyword",
                "size": 100
            }
        }
    }
}


# counting objects in periods

def objectsByPeriods(objectList,interval):

    # preparing object filters for query
    aggregations = {}
    def prepareQuery(objectList):
        for object in objectList:
            aggregations[object] = {"filter": {"match_phrase": {"detected_objects.object": object}}}
    prepareQuery(objectList)

    # completing query
    artworksByPeriod = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "must": {
                                "exists": {
                                    "field": "detected_objects"
                                }
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {"match_phrase": {"work_type": "graphic print"}},
                                {"match_phrase": {"work_type": "painting"}},
                                {"match_phrase": {"work_type": "drawing"}}
                            ]
                        }
                    }
                ]
            }
        },
        "aggs": {
            "periods": {
                "aggs": aggregations
                ,
                "histogram": {
                    "field": "date_latest",
                    "interval": interval
                }
            }
        }
    }
    countAll = callElastic(artworksByPeriod)['aggregations']['periods']['buckets'] # Gets count of all artworks in specific periods

    relatedPeriods = []
    for periodSet in countAll: # Gets labels
        if periodSet['doc_count'] > config.minArtworksLimit or len(relatedPeriods) > 0: # cuts periods with small number of artworks but only from beginning of timeline
            relatedPeriods.append(periodSet['key'])

    totalArtworks = [periodSet['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods] # check if period is in relatedPeriods and if so, it adds count to totoal artworks

    artworksInPeriod = {'periods': relatedPeriods, 'totalArtworks': totalArtworks, 'artworksWithObject': []}

    for object in objectList:
        artworksWithObject = [periodSet[object]['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods]  # check if period is in relatedPeriods and if so, it adds count to related artworks
        objectPercents = [round(artworksWithObject[item] / totalArtworks[item], 3) * 100 for item in range(len(totalArtworks))]  # Counting percent of artworks copntained selected object in comparison with total artworks
        artworksInPeriod['artworksWithObject'].append([object, artworksWithObject, objectPercents])

    return artworksInPeriod


'''

randomObjectType = randrange(len(objectTypes)) # Selecting Random Object Type
if config.searchedObject == None:
    searchedObject = objectTypes[randomObjectType]
else:
    searchedObject = config.searchedObject
artworksForSorting = getArtworksByObject(searchedObject)
artworksSorted = sorted(artworksForSorting, key=sorter, reverse=True)[:config.maxGallerySize]
collectionsSum = callElastic(getCollectionsSum)['aggregations']['galleries_sum']['buckets']
artworksInPeriod = objectsByPeriods([searchedObject],config.periodLength)
for i in artworksInPeriod:
    print(i)
'''


# Flask

from app import app
from flask import render_template

@app.route('/')
def index():
    randomObjectType = randrange(len(objectTypes)) # Selecting Random Object Type
    if config.searchedObject == None:
        searchedObject = objectTypes[randomObjectType]
    else:
        searchedObject = config.searchedObject
    artworksForSorting = getArtworksByObject(searchedObject)
    artworksSorted = sorted(artworksForSorting, key=sorter, reverse=True)[:config.maxGallerySize]
    collectionsSum = callElastic(getCollectionsSum)['aggregations']['galleries_sum']['buckets']
    artworksInPeriod = objectsByPeriods(['man','woman','boy','girl'],config.periodLength)
    return render_template('index.html',
                           artworksForWeb=artworksSorted,
                           searchedObject=searchedObject,
                           collectionsSum=collectionsSum,
                           artworksInPeriod=artworksInPeriod
                           )
@app.route('/test')
def test():
    return render_template('test.html')

