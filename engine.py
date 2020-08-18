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


# GET RANDOM OBJECT TYPES

def getRandomObjectTypes(countOfObjects):

    objectTypesQuery = {
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

    objectTypesDict = callElastic(objectTypesQuery)
    objectTypes = []

    # Selecting object types with more than 10 presences
    for object in objectTypesDict['aggregations']['Total mediums']['buckets']:
        if object['doc_count'] >= config.minObjectsLimit:
            objectTypes.append(object['key'])

    randomObjects = []
    for i in range(countOfObjects):
        randomObjects.append(objectTypes[randrange(len(objectTypes))])

    return randomObjects


# GET ARTWORKS BY OBJECT

def getArtworksByObject(objectList):

    allListsResult = []

    def sorter(artwork):
        score = artwork['_source']['top_object_score']
        return score

    for searchedObject in objectList:

        # Preparing the part of the query where contained object conditions are defined
        mustObjectsQuery = [
            {
                "bool": {
                    "must": [
                        {"exists": {"field": "detected_objects"}},
                        {
                            "bool": {
                                "should": [
                                    {"match_phrase": {"work_type": "graphic"}},
                                    {"match_phrase": {"work_type": "painting"}},
                                    {"match_phrase": {"work_type": "drawing"}}
                                ]
                            }
                        }
                    ]
                }
            }
        ]

        # Looking at input - if it is list of objects or single object
        if type(searchedObject) == dict:
            for key in searchedObject:
                key = key
            objectGroup = searchedObject[key]
            for object in objectGroup:
                mustObjectsQuery.append({"match_phrase": {"detected_objects.object": object}})
        else:
            mustObjectsQuery.append({"match_phrase": {"detected_objects.object": searchedObject}})

        queryForArtworks = {
            "size": 1000,
            "query": {
                "bool": {
                    "must": mustObjectsQuery # includes above defined mustObjectQuery
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
                    "date_earliest",
                    "date_latest"
                ]
            }
        }
        artworks = callElastic(queryForArtworks)['hits']['hits']
        # print(searchedObject + ': '+ str(len(artworks)) + ' results')

        # expanding data by imageUrl and topObjectScore

        expandedArtworks = []

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
                if type(searchedObject) == dict:
                    for key in searchedObject:
                        key = key
                    searchedObject = searchedObject[key][0] # If it is object group the topObjectScore is selected by first object in the group
                print(objectSet['object'], searchedObject)
                if objectSet['object'] == searchedObject and objectSet['score'] >= topObjectScore:
                    topObjectScore = objectSet['score']
            artwork['_source']['top_object_score'] = topObjectScore
            expandedArtworks.append(artwork)

        # sorts expandedArtworks by topObjectScore
        sortedArtworks = sorted(expandedArtworks, key=sorter, reverse=True)[:config.maxGallerySize]
        allListsResult.append(sortedArtworks)

    return allListsResult

# AGGREGATIONS BY PERIODS

def objectsByPeriods(objectList,interval):

    # preparing object filters for query
    aggregations = {}
    def prepareQuery(objectList):
        counter = 1
        for searchedObject in objectList:
            if type(searchedObject) == dict:
                for key in searchedObject:
                    groupName = key
                mustList = []
                for object in searchedObject[groupName]:
                    mustList.append({"match_phrase": {"detected_objects.object": object}})
                groupAggregation = {
                    "filter": {
                        "bool": {
                            "must": mustList
                        }
                    }
                }
                aggregations[groupName] = groupAggregation
                counter +=1
            else:
                aggregations[searchedObject] = {"filter":{"match_phrase": {"detected_objects.object": searchedObject}}}

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

        if type(object) == dict:
            objectName = ""
            for key in object:
                objectName = key
            artworksWithObject = [periodSet[objectName]['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods]  # check if period is in relatedPeriods and if so, it adds count to related artworks
        else:
            objectName=object
            artworksWithObject = [periodSet[object]['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods]  # check if period is in relatedPeriods and if so, it adds count to related artworks
        objectPercents = [round(artworksWithObject[item] / totalArtworks[item], 3) * 100 for item in range(len(totalArtworks))]  # Counting percent of artworks copntained selected object in comparison with total artworks
        artworksInPeriod['artworksWithObject'].append([objectName, artworksWithObject, objectPercents])

    return artworksInPeriod

# GET COLLECTION SUM

def getCollectionsSum():
    collectionsQuery = {
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
    collectionsSum = callElastic(collectionsQuery)['aggregations']['galleries_sum']['buckets']
    return collectionsSum

'''
collections = getArtworksByObject(config.searchedObjects)
for collection in collections:
    print(len(collection))

print(objectsByPeriods(config.searchedObjects,100))
print(getRandomObjectTypes(3))
print(getCollectionsSum())
'''
