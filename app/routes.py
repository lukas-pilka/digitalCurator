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
    artworksSorted = engine.getArtworksByObject(searchedObjects)
    collectionsSum = engine.getCollectionsSum()
    artworksInPeriod = engine.objectsByPeriods(searchedObjects, config.periodLength)
    groupNames = [] # Clearing because dicts between searched objects
    for object in searchedObjects:
        if type(object) == dict:
            object = next(iter(object))
            groupNames.append(object)
        else:
            groupNames.append(object)
    print(groupNames)
    return render_template('index.html',
                           artworksForWeb=artworksSorted,
                           searchedObjects=groupNames,
                           collectionsSum=collectionsSum,
                           artworksInPeriod=artworksInPeriod
                           )
@app.route('/test')
def test():
    return render_template('test.html')
