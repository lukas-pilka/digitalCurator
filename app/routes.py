# IMPORTS


import config
import engine

# Flask

from app import app
from flask import render_template

@app.route('/')
def index():
    # Selecting objects for detection
    if config.searchedObjects == None:
        searchedObjects = engine.getRandomObjectTypes(config.countOfRandomObjects)
    else:
        searchedObjects = config.searchedObjects
    artworksSorted = engine.getArtworksByObject(searchedObjects, config.dateFrom, config.dateTo)
    titleImage = artworksSorted[0][0]
    artworksInPeriod = engine.objectsByPeriods(searchedObjects, config.periodLength, config.dateFrom, config.dateTo)
    collectionsByPeriods = engine.devideCollectionByPeriods(artworksInPeriod, artworksSorted)
    collectionsSum = engine.getCollectionsSum()
    collectionTitles = [] # Clearing because dicts between searched objects
    for collection in searchedObjects:
        collectionTitles.append(list(collection.keys())[0])
    return render_template('index.html',
                           artworksForWeb=collectionsByPeriods,
                           searchedObjects=collectionTitles,
                           collectionsSum=collectionsSum,
                           artworksInPeriod=artworksInPeriod,
                           titleImage=titleImage
                           )
@app.route('/test')
def test():
    return render_template('test.html')
