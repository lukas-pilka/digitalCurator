# IMPORTS

import config
import engine

from urllib.parse import urlparse

# Flask

from app import app
from flask import render_template, g, flash, url_for, redirect, request

# Forms
from .forms import SearchForm
app.config['SECRET_KEY'] = 'you-will-never-guess'

import time
@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

    # Nastavit defaultni promenne
    # Byly peromenne odeslane jako get - prepiseme defaultni promennew
    # Nastavirt default value do formulare
    # Vykreslit stranku

# Returns exhibition by config
@app.route('/', methods=['GET', 'POST'])
def exhibition():
    form = SearchForm()
    if form.validate_on_submit(): # If user submit to form it redirects with arguments
        exName = form.exhibitionName.data
        exDisplayedObjects = form.searchedClassSelect.data # Loads list of classes from select multiple choices
        exComparisonObjects = form.comparisonClassSelect.data  # Loads list of classes from select multiple choices
        exDateFrom = form.dateFrom.data  # Loads dateFrom from select
        exDateTo = form.dateTo.data  # Loads dateTo from select
        return redirect(url_for('exhibition', exName=exName, exDisplayedObjects=exDisplayedObjects, exComparisonObjects=exComparisonObjects, exDateFrom=exDateFrom, exDateTo=exDateTo))
    else:
        if len(request.args.to_dict(flat=False)) > 0: # If it receives arguments It proceeds and render exhibition
            exParams = request.args.to_dict(flat=False) # It parses arguments from url
            exName = exParams['exName'][0]
            dateFrom = int(exParams['exDateFrom'][0])
            dateTo = int(exParams['exDateTo'][0])
            exhibitionsList = [{exName: [[displayedObject] for displayedObject in exParams['exDisplayedObjects']]}]
            try:
                exhibitionsList.append({exName+' 2': [[comparisonObject] for comparisonObject in exParams['exComparisonObjects']]})
            except:
                pass

        else: # If It hasn't receive arguments
            dateFrom = config.dateFrom
            dateTo = config.dateTo
            if config.exhibitionsList == None:
                exhibitionsList = engine.getRandomObjectTypes(config.countOfRandomObjects)
            else:
                exhibitionsList = config.exhibitionsList

        artworksInPeriod = engine.getPeriodData(exhibitionsList, config.periodLength, dateFrom, dateTo)
        artworksSorted = engine.getArtworksByObject(exhibitionsList, dateFrom, dateTo)
        titleImage = artworksSorted[0][0]
        collectionsByPeriods = engine.devideCollectionByPeriods(artworksInPeriod, artworksSorted)
        galleriesSum = engine.getGalleriesSum()
        collectionTitles = []  # Clearing because dicts between searched objects
        for collection in exhibitionsList:
            collectionTitles.append(list(collection.keys())[0])
        return render_template('index.html',
                               artworksForWeb=collectionsByPeriods,
                               searchedObjects=collectionTitles,
                               galleriesSum=galleriesSum,
                               artworksInPeriod=artworksInPeriod,
                               titleImage=titleImage,
                               form=form,
                               )


