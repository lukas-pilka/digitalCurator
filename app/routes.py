# IMPORTS


import config
import engine

# Flask

from app import app
from flask import render_template, g

import time
@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

@app.route('/')
def index():
    # Selecting objects for detection
    if config.exhibitionsList == None:
        exhibitionsList = engine.getRandomObjectTypes(config.countOfRandomObjects)
    else:
        exhibitionsList = config.exhibitionsList
    artworksSorted = engine.getArtworksByObject(exhibitionsList)
    titleImage = artworksSorted[0][0]
    artworksInPeriod = engine.objectsByPeriods(exhibitionsList, config.periodLength, config.dateFrom, config.dateTo)
    collectionsByPeriods = engine.devideCollectionByPeriods(artworksInPeriod, artworksSorted)
    galleriesSum = engine.getGalleriesSum()
    collectionTitles = [] # Clearing because dicts between searched objects
    for collection in exhibitionsList:
        collectionTitles.append(list(collection.keys())[0])
    return render_template('index.html',
                           artworksForWeb=collectionsByPeriods,
                           searchedObjects=collectionTitles,
                           galleriesSum=galleriesSum,
                           artworksInPeriod=artworksInPeriod,
                           titleImage=titleImage
                           )
@app.route('/test')
def test():
    return render_template('test.html')
