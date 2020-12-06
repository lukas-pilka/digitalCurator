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

    # Set default values of exhibition from config
    exDateFrom = config.dateFrom
    exDateTo = config.dateTo
    galleriesSum = engine.getGalleriesSum()
    if config.exhibitionsList == None:
        exhibitionsList = engine.getRandomObjectTypes(config.countOfRandomObjects)
    else:
        exhibitionsList = config.exhibitionsList
    exName = [key for key in exhibitionsList[0].keys()][0]  # Get exhibition name from name of the first dict

    # After form submit it posts values into url attributes and redirect to start
    if form.validate_on_submit():
        exName = form.exhibitionName.data
        exDisplayedObjects = form.searchedClassSelect.data # Loads list of classes from select multiple choices
        exComparisonObjects = form.comparisonClassSelect.data  # Loads list of classes from select multiple choices
        exDateFrom = form.dateFrom.data  # Loads exDateFrom from select
        exDateTo = form.dateTo.data  # Loads exDateTo from select
        return redirect(url_for('exhibition', exName=exName, exDisplayedObjects=exDisplayedObjects, exComparisonObjects=exComparisonObjects, exDateFrom=exDateFrom, exDateTo=exDateTo))

    # If it receives arguments it overwrites default values
    if len(request.args.to_dict(flat=False)) > 0:
        exParams = request.args.to_dict(flat=False) # It parses arguments from url
        exName = exParams['exName'][0]
        exDateFrom = int(exParams['exDateFrom'][0])
        exDateTo = int(exParams['exDateTo'][0])

        # preparing name of 1st collection
        if len(exParams['exDisplayedObjects']) > 1:
            set1Name = ', '.join(exParams['exDisplayedObjects'][:-1]) +" and "+ (exParams['exDisplayedObjects'][-1])
        else:
            set1Name = exParams['exDisplayedObjects'][0]

        exhibitionsList = [{ set1Name: [[displayedObject] for displayedObject in exParams['exDisplayedObjects']]}]
        try:
            # preparing name of 2nd collection
            if len(exParams['exComparisonObjects']) > 1:
                set2Name = ', '.join(exParams['exComparisonObjects'][:-1]) +" and "+ (exParams['exComparisonObjects'][-1])
            else:
                set2Name = exParams['exComparisonObjects'][0]
            exhibitionsList.append({set2Name: [[comparisonObject] for comparisonObject in exParams['exComparisonObjects']]})
        except:
            pass

    artworksInPeriod = engine.getPeriodData(exhibitionsList, config.periodLength, exDateFrom, exDateTo)
    artworksSorted = engine.getArtworksByObject(exhibitionsList, exDateFrom, exDateTo)

    # Check for zero results
    if len(artworksSorted[0]) == 0:
        return render_template('index.html',
                               exName=exName,
                               galleriesSum=galleriesSum,
                               artworksInPeriod=artworksInPeriod,
                               form=form,
                               )

    else:
        titleImage = artworksSorted[0][0]
        collectionsByPeriods = engine.devideCollectionByPeriods(artworksInPeriod, artworksSorted)
        collectionTitles = []  # Clearing because dicts between searched objects
        for collection in exhibitionsList:
            collectionTitles.append(list(collection.keys())[0])
        return render_template('index.html',
                               exName=exName,
                               artworksForWeb=collectionsByPeriods,
                               searchedObjects=collectionTitles,
                               galleriesSum=galleriesSum,
                               artworksInPeriod=artworksInPeriod,
                               titleImage=titleImage,
                               form=form,
                               )

@app.route('/noresult/')
def noresult():
    return render_template('noresult.html')


