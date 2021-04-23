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

def getRandomObjectTypes():
    comparisonSets = config.depository
    randomSetIndex = randrange(len(config.depository))
    if config.preSelectedExhibition != False:
        return config.preSelectedExhibition
    else:
        return comparisonSets[randomSetIndex]

# PREPARING EXHIBITION QUERY
# Common properties for getArtworksByObject and getPeriodData

def exhibitionPropertiesQuery(dateFrom, dateTo):
    return [
        {
            "bool": {
                "should": [
                    {"match_phrase": {"work_type": "graphic"}},
                    {"match_phrase": {"work_type": "painting"}},
                    {"match_phrase": {"work_type": "drawing"}}
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

# Common properties for getArtworksByObject query and getPeriodData aggregations
def prepareExhibitionKeywordQuery(exhibition):

    exhibitionKeywordsQuery = []

    # Adding match_phrase conditions to must query list. One for each object.
    exhibitionName = list(exhibition.keys())[0]
    exhibitionParams = exhibition[exhibitionName]
    for keywordsGroup in exhibitionParams:  # expanding exhibitionQuery from collection (exhibitionParams)
        keywordsQuery = []
        for keyword in keywordsGroup:  # expanding keywordsQuery from keywordsGroup
            keywordsQuery.append(
                {
                    "nested": {
                        "path": "detected_objects",
                        "query": {
                            "bool": {
                                "must": [
                                    {"match": {"detected_objects.object": keyword}},
                                    {"range": {"detected_objects.score": {"gt": config.scoreThreshold}}}
                                ]
                            }
                        }
                    }
                })
        exhibitionKeywordsQuery.append({"bool": {"should": keywordsQuery}})

    return exhibitionKeywordsQuery

# GET ARTWORKS BY OBJECT

def getArtworksByObject(exhibitionList, dateFrom, dateTo):

    # preparing interval
    interval = prepareInterval(dateFrom, dateTo)
    print('Interval: ' + str(interval))

    allListsResult = []

    def sorter(artwork):
        score = artwork['_source']['average_score']
        return score

    for exhibition in exhibitionList:
        exhibitionKeywordsQuery = prepareExhibitionKeywordQuery(exhibition)
        exhibitionQuery = exhibitionPropertiesQuery(dateFrom, dateTo) + exhibitionKeywordsQuery

        # Only free artworks
        if config.onlyFreeArtworks == True:
            exhibitionQuery.append({"bool": {"must": [{"term": {"is_free": True}}]}})

        #  exhibitionQuery # includes above defined exhibitionQuery
        # Completing query
        requestForArtworks = {
            "size": 1000,
            "query":{
                "bool": {
                    "must": exhibitionQuery # includes above defined exhibitionQuery
                }
            },
            "aggs": {
                "periods": {
                    "histogram": {
                        "field": "date_latest",
                        "interval": interval
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

        print('Request for artworks: ' + str(requestForArtworks))

        # Calling elastic database with completed query
        rawData = callElastic(requestForArtworks)
        artworks = rawData['hits']['hits']

        # expanding data by imageUrl and topObjectScore
        expandedArtworks = []

        for artwork in artworks:
            print(artwork)
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
            exhibitionName = list(exhibition.keys())[0]
            for elementaryObjects in exhibition[exhibitionName]:

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

    return allListsResult

# PREPARE INTERVAL

def prepareInterval(dateFrom, dateTo):
    rawInterval = (dateTo - dateFrom) / 7
    if rawInterval > 100:
        interval = 100
    elif rawInterval > 50:
        interval = 50
    elif rawInterval > 25:
        interval = 25
    elif rawInterval > 10:
        interval = 10
    else:
        interval = int(round(rawInterval, 0))
    return interval

# AGGREGATIONS BY PERIODS

def getPeriodData(exhibitionsList, dateFrom, dateTo):

    # preparing interval
    interval = prepareInterval(dateFrom, dateTo)
    print('Interval: ' + str(interval))

    # preparing object filters for query
    aggregations = {}
    def prepareQuery(exhibitionsList):
        counter = 1
        for exhibition in exhibitionsList:
            exhibitionQuery = prepareExhibitionKeywordQuery(exhibition)
            groupAggregation = {
                "filter": {
                    "bool": {
                        "must": exhibitionQuery
                    }
                }
            }
            exhibitionName = list(exhibition.keys())[0]
            aggregations[exhibitionName] = groupAggregation
            counter +=1

    prepareQuery(exhibitionsList)

    # completing query
    requestForPeriodData = {
        "size": 0,
        "query": {
            "bool": {
                "must": exhibitionPropertiesQuery(dateFrom,dateTo+interval)
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
    print('Request for periods data: ' + str(requestForPeriodData))
    countAll = callElastic(requestForPeriodData)['aggregations']['periods']['buckets'] # Gets count of all artworks in specific periods
    print(countAll)

    periodStarts = [int(periodSet['key']) for periodSet in countAll]
    periodNames = [str(periodStart)+' - '+str(periodStart+interval) for periodStart in periodStarts]
    totalArtworks = [periodSet['doc_count'] for periodSet in countAll if periodSet['key'] in periodStarts] # check if period is in relatedPeriods and if so, it adds count to totoal artworks
    artworksInPeriod = {'periodStarts': periodStarts, 'periodNames':periodNames, 'totalArtworks': totalArtworks, 'artworksWithObject': [], 'interval': interval}

    for object in exhibitionsList:
        objectName = list(object.keys())[0]
        artworksWithObject = [periodSet[objectName]['doc_count'] for periodSet in countAll if periodSet['key'] in periodStarts]  # check if period is in relatedPeriods and if so, it adds count to related artworks
        objectPercents = []
        for item in range(len(totalArtworks)):
            if totalArtworks[item] == 0: # Eliminates dividing by zero error
                objectPercents.append(0)
            else:
                objectPercents.append(round(artworksWithObject[item] / totalArtworks[item], 6) * 100)  # Counting percent of artworks copntained selected object in comparison with total artworks
        artworksInPeriod['artworksWithObject'].append([objectName, artworksWithObject, objectPercents])

    print('Resulting periods data: ' + str(artworksInPeriod))
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
                },
            },
            "free_sum": {
                "terms": {
                    "field": "is_free"
                }
            }
        }
    }
    rawData = callElastic(collectionsQuery)['aggregations']
    galleriesData = rawData['galleries_sum']['buckets']
    freeArtworksCount = rawData['free_sum']['buckets'][1]['doc_count']
    galleriesCount = len(galleriesData)
    artworksCount = 0
    for gallery in galleriesData:
        artworksCount += gallery['doc_count']
    summary = {'galleries count': galleriesCount, 'artworks count': artworksCount, 'free artworks count': freeArtworksCount}
    return summary

# GET DETECTED OBJECT LIST

def getDetectedObjectsList():
    collectionsQuery = {
        "size": 0,
        "query": {
            "bool": {
                "should": [
                    {
                        "match_phrase": {
                            "work_type": "graphic"
                        }
                    },
                    {
                        "match_phrase": {
                            "work_type": "painting"
                        }
                    },
                    {
                        "match_phrase": {
                            "work_type": "drawing"
                        }
                    }
                ]
            }
        },
        "aggs": {
            "detected_objects_list": {
                "nested": {
                    "path": "detected_objects"
                },
                "aggs": {
                    "object_categories": {
                        "filter": {
                            "range": {"detected_objects.score": {"gt": config.scoreThreshold}}
                        },
                        "aggs": {
                            "filtered_by_threshold":{
                                "terms": {
                                    "field": "detected_objects.object.keyword",
                                    "size": 10000
                                },
                                "aggs": {
                                    "artworks_count": {
                                        "reverse_nested": {}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    DetectedObjectClassesList = callElastic(collectionsQuery)['aggregations']['detected_objects_list']['object_categories']['filtered_by_threshold']['buckets']
    TuplesClassesList = []
    for objectClass in DetectedObjectClassesList:
        relatedArtworksCount = str(objectClass["artworks_count"]['doc_count'])
        TuplesClassesList.append((objectClass['key'],objectClass['key']+' ('+relatedArtworksCount +')'))
    return TuplesClassesList

# DEVIDE EVERY COLLECTION BY PERIODS AND SORTS ARTWORKS INTO SPECIFIC PERIOD BY ITS DATE EARLIEST
def sortCollectionByPeriods(objectsByPeriods, getArtworksByObject):
    sortedCollections = []

    for collection in getArtworksByObject:
        collectionPeriodsList = []

        for period in objectsByPeriods['periodStarts']:
            periodStart = period
            periodEnd = periodStart + objectsByPeriods['interval']
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

# PREPARES NAME OF COLLECTION
def prepareName(listOfNames):
    if len(listOfNames) > 1:
        setName = ', '.join(listOfNames[:-1]) +" and "+ (listOfNames[-1])
    else:
        setName = listOfNames[0]
    return setName

# CREATES DICT WITH ARGUMENTS FOR url_for
def createArguments(exhibition):
    arguments = {}
    arguments['exName'] = exhibition['name']
    arguments['exDateFrom'] = exhibition['dateFrom']
    arguments['exDateTo'] = exhibition['dateTo']
    arguments['exDisplayedObjects'] = exhibition['displayedObjects'][0]
    # tests whether data comparison objects exists in defaultExhibition
    if len(exhibition['displayedObjects']) > 1:
        arguments['exComparisonObjects'] = exhibition['displayedObjects'][1]
    else:
        arguments['exComparisonObjects'] = None
    return arguments

#print(getDetectedObjectsList())
#getArtworksByObject([{'Tree, Plant and Castle': [['Tree', 'Plant'], ['Castle']]}], 1500,1900)
#getPeriodData([{'Angel': [['Angel']]}], 1000, 2000)
#print(getRandomObjectTypes())
#print(getGalleriesSum())


