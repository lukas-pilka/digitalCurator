import requests
from requests.auth import HTTPBasicAuth
from random import randrange
import json
import config

# CONNECTION TO ELASTIC SEARCH

def callElastic(query):
    payload = ""
    rawData = requests.get(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks3/_search',
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    return (dataDict)

# GET RANDOM OBJECT TYPES

def getRandomObjectTypes(requestedCountOfCollections):

    comparisonSets = config.depositary
    randomSetIndex = randrange(len(comparisonSets))
    selectedComparisonSet = comparisonSets[randomSetIndex]
    randomExhibition = []

    for collection in range(requestedCountOfCollections):
        randomCollectionIndex = randrange(len(selectedComparisonSet))
        if not selectedComparisonSet[randomCollectionIndex] in randomExhibition:
            randomExhibition.append(selectedComparisonSet[randomCollectionIndex])

    return randomExhibition

# GET ARTWORKS BY OBJECT

def getArtworksByObject(objectList, dateFrom, dateTo):

    allListsResult = []

    def sorter(artwork):
        score = artwork['_source']['average_score']
        return score

    for searchedObject in objectList:

        # Preparing the part of the query where object conditions are defined
        mustObjectsQuery = [
            {
                "bool": {
                    "must": [
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
            },
            {
                "range": {
                    "date_latest": {
                        "gte": dateFrom,
                        "lt": dateTo
                    }
                }
            }
        ]

        # Adding match_phrase conditions to must query list. One for each object.
        exhibitionName = list(searchedObject.keys())[0]
        exhibitionParams = searchedObject[exhibitionName]
        for keywordsGroup in exhibitionParams: #expanding sholud lists from collection (exhibitionParams)
            shouldObjectList = []
            for keyword in keywordsGroup: #expanding sholud objects from keywordsGroup (Should List)
                shouldObjectList.append({"bool": {
                    "must": [
                        {"match": {"detected_objects.object": keyword}},
                        {"range": {"detected_objects.score": {"gt": config.keywordProbabilityMin}}}
                    ]
                }})
            mustObjectsQuery.append({"nested": {"path": "detected_objects", "query": {"bool": {"should": shouldObjectList}}}})

        if config.onlyFreeArtworks == True:
            mustObjectsQuery.append({"bool": {"must": [{"term": {"is_free": True}}]}})

        # Completing query
        queryForArtworks = {
            "size": 2000,
            "query": {
                "bool": {
                    "must": mustObjectsQuery # includes above defined mustObjectQuery
                }
            },
            "aggs": {
                "periods": {
                    "histogram": {
                        "field": "date_latest",
                        "interval": 100
                    }
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

        # Calling elastic database with completed query
        rawData = callElastic(queryForArtworks)
        artworks = rawData['hits']['hits']

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

            # selects searched object with highest score on image and saves it to topElementaryObjectScoreSum (It's useful for sorting)
            searchedObjectsScore = [] # saves highest probability achieved for each object
            #print('---next artwork---')
            for elementaryObjects in searchedObject[exhibitionName]:

                for elementaryObject in elementaryObjects:

                    topElementaryObjectScore = 0
                    for detectedObject in artwork['_source']['detected_objects']:
                        if elementaryObject == detectedObject['object'] and detectedObject['score'] >= topElementaryObjectScore: # If it searched elementaryObject and if is higher than topElementaryObjectScore
                            topElementaryObjectScore = detectedObject['score']

                    searchedObjectsScore.append(topElementaryObjectScore)
                    #print(elementaryObject, topElementaryObjectScore)

            artwork['_source']['searched_object'] = exhibitionName
            artwork['_source']['average_score'] = round(sum(searchedObjectsScore) / len(searchedObjectsScore), 2) # get percents
            expandedArtworks.append(artwork)

        # sorts expandedArtworks by topObjectScore
        sortedArtworks = sorted(expandedArtworks, key=sorter, reverse=True)[:config.maxGallerySize]
        allListsResult.append(sortedArtworks)

        # expanding aggregations
        aggregations = rawData['aggregations']['periods']['buckets']
        for period in aggregations:
            print(period)

    return allListsResult

# AGGREGATIONS BY PERIODS

def objectsByPeriods(objectList,interval,dateFrom,dateTo):

    # preparing object filters for query
    aggregations = {}
    def prepareQuery(objectList):
        counter = 1
        for searchedObject in objectList:
            groupName = list(searchedObject.keys())[0]
            mustList = []

            for shouldGroup in searchedObject[groupName]:
                shouldObjectList = []
                for shouldObject in shouldGroup:
                    shouldObjectList.append({"match_phrase": {"detected_objects.object": shouldObject}})

                mustList.append({"bool": {"should": shouldObjectList}})


            groupAggregation = {
                "filter": {
                    "bool": {
                        "must": mustList
                    }
                }
            }
            aggregations[groupName] = groupAggregation
            counter +=1

    prepareQuery(objectList)

    # completing query
    artworksByPeriod = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {
                        "range": {
                            "date_latest": {
                                "gte": dateFrom,
                                "lt": dateTo
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
    print(artworksByPeriod)
    countAll = callElastic(artworksByPeriod)['aggregations']['periods']['buckets'] # Gets count of all artworks in specific periods

    relatedPeriods = []
    for periodSet in countAll: # Gets labels
        if periodSet['doc_count'] > config.minArtworksLimit or len(relatedPeriods) > 0: # cuts periods with small number of artworks but only from beginning of timeline
            relatedPeriods.append(periodSet['key'])

    totalArtworks = [periodSet['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods] # check if period is in relatedPeriods and if so, it adds count to totoal artworks

    artworksInPeriod = {'periods': relatedPeriods, 'totalArtworks': totalArtworks, 'artworksWithObject': []}

    for object in objectList:
        objectName = list(object.keys())[0]
        artworksWithObject = [periodSet[objectName]['doc_count'] for periodSet in countAll if periodSet['key'] in relatedPeriods]  # check if period is in relatedPeriods and if so, it adds count to related artworks
        objectPercents = [round(artworksWithObject[item] / totalArtworks[item], 3) * 100 for item in range(len(totalArtworks))]  # Counting percent of artworks copntained selected object in comparison with total artworks
        artworksInPeriod['artworksWithObject'].append([objectName, artworksWithObject, objectPercents])

    return artworksInPeriod

# GET COLLECTION SUM

def getGalleriesSum():
    collectionsQuery = {
        "size": 0,
        "aggs": {
            "galleries_sum": {
                "terms": {
                    "field": "gallery.keyword",
                    "size": 1000
                }
            }
        }
    }
    galleriesData = callElastic(collectionsQuery)['aggregations']['galleries_sum']['buckets']
    galleriesCount = len(galleriesData)
    artworksCount = 0
    for gallery in galleriesData:
        artworksCount += gallery['doc_count']
    summary = {'galleries count': galleriesCount, 'artworks count': artworksCount}
    return summary

# DEVIDE EVERY COLLECTION BY PERIODS AND SORTS ARTWORKS INTO SPECIFIC PERIOD BY ITS DATE EARLIEST
def devideCollectionByPeriods(objectsByPeriods, getArtworksByObject):
    sortedCollections = []

    for collection in getArtworksByObject:
        collectionPeriodsList = []

        for period in objectsByPeriods['periods']:
            periodStart = int(period)
            periodEnd = int(periodStart) + config.periodLength
            periodName = str(periodStart) +' - '+ str(periodEnd)
            periodArtworksList = []

            for artwork in collection:
                artworkDatation = artwork['_source']['date_earliest']
                if artworkDatation >= periodStart and artworkDatation < periodEnd:
                    periodArtworksList.append(artwork)

            if len(periodArtworksList) > 0:
                collectionPeriod = {periodName: periodArtworksList}
                collectionPeriodsList.append(collectionPeriod)

        sortedCollections.append(collectionPeriodsList)

    return sortedCollections




getArtworksByObject(config.searchedObjects, config.dateFrom, config.dateTo)
print(objectsByPeriods(config.searchedObjects,100, config.dateFrom, config.dateTo))
print(getRandomObjectTypes(3))
print(getGalleriesSum())


