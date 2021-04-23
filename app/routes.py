# IMPORTS

import config
import engine

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

# Returns exhibition
@app.route('/', methods=['GET', 'POST'])
def exhibition():
    form = SearchForm()
    galleriesSum = engine.getGalleriesSum()

    # Extends browse exhibitions by parsed url
    browseExhibitions = []
    for exhibition in config.depository:
        arguments = engine.createArguments(exhibition)
        url = str(url_for('exhibition', exName=arguments['exName'], exDisplayedObjects=arguments['exDisplayedObjects'],
                exComparisonObjects=arguments['exComparisonObjects'], exDateFrom=arguments['exDateFrom'],
                exDateTo=arguments['exDateTo']))
        exhibition['url'] = url
        browseExhibitions.append(exhibition)

    # If it doesn't receive arguments it set arguments with default values of exhibition from config
    receivedArguments = request.args.to_dict(flat=False)

    if 'exDisplayedObjects' not in receivedArguments: # Condition is based on presence of Displayed objects (not on presence of arguments because different arguments can exist)
        arguments = engine.createArguments(engine.getRandomObjectTypes())
        return redirect(url_for('exhibition', exName=arguments['exName'], exDisplayedObjects=arguments['exDisplayedObjects'],
                                exComparisonObjects=arguments['exComparisonObjects'], exDateFrom=arguments['exDateFrom'], exDateTo=arguments['exDateTo']))

    # If it receives arguments it overwrites default values
    if 'exDisplayedObjects' in receivedArguments:
        exDisplayedObjectsNotParsed = request.args.getlist('exDisplayedObjects') # it returns strings instead of lists, parsing is necessary
        exDisplayedObjects = [i.strip("[]").replace("'", "").split(', ') for i in exDisplayedObjectsNotParsed] # Parsing - geting lists from strings
        exParams = request.args.to_dict(flat=False) # It parses arguments from url
        exName = exParams['exName'][0]
        exDateFrom = int(exParams['exDateFrom'][0])
        exDateTo = int(exParams['exDateTo'][0])
        set1Name = engine.prepareName(sum(exDisplayedObjects, []))
        exhibitionsList = [{set1Name: [displayedObject for displayedObject in exDisplayedObjects]}]

        # tests whether data comparison objects exists in arguments
        try:
            exComparisonObjectsNotParsed = request.args.getlist('exComparisonObjects')  # it returns strings instead of lists, parsing is necessary
            exComparisonObjects = [i.strip("[]").replace("'", "").split(', ') for i in exComparisonObjectsNotParsed]  # Parsing - geting lists from strings
            set2Name = engine.prepareName(sum(exComparisonObjects, []))
            exhibitionsList.append({set2Name: [comparisonObject for comparisonObject in exComparisonObjects]})
        except:
            pass

    print('---------')
    print(exName)
    print(exDateFrom, exDateTo)
    print(exhibitionsList)
    print('---------')

    # After form submit it posts values into url attributes and redirect to start
    if form.validate_on_submit():
        if len(form.exhibitionName.data) > 0:
            exName = form.exhibitionName.data
        else:
            exName = "Digital curator's choice"
        exDisplayedObjects = form.searchedClassSelect.data  # Loads list of classes from select multiple choices
        exComparisonObjects = form.comparisonClassSelect.data  # Loads list of classes from select multiple choices
        exDateFrom = form.dateFrom.data  # Loads exDateFrom from select
        exDateTo = form.dateTo.data  # Loads exDateTo from select
        return redirect(url_for('exhibition', exName=exName, exDisplayedObjects=exDisplayedObjects,
                                exComparisonObjects=exComparisonObjects, exDateFrom=exDateFrom, exDateTo=exDateTo))

    # Sending request to Elastic
    artworksInPeriod = engine.getPeriodData(exhibitionsList, exDateFrom, exDateTo)
    artworksSorted = engine.getArtworksByObject(exhibitionsList, exDateFrom, exDateTo)
    print('--------artworksInPeriod--------')
    print(artworksInPeriod)

    # Check for zero results
    if len(artworksSorted[0]) == 0:
        return render_template('index.html',
                               exName=exName,
                               galleriesSum=galleriesSum,
                               artworksInPeriod=artworksInPeriod,
                               browseExhibitions=browseExhibitions,
                               form=form,
                               )

    else:
        titleImage = artworksSorted[0][0]
        collectionsByPeriods = engine.sortCollectionByPeriods(artworksInPeriod, artworksSorted)
        collectionTitles = []  # Clearing because dicts between searched objects
        for collection in exhibitionsList:
            collectionTitles.append(list(collection.keys())[0])
        return render_template('index.html',
                               exName=exName,
                               artworksForWeb=collectionsByPeriods,
                               searchedObjects=collectionTitles,
                               galleriesSum=galleriesSum,
                               artworksInPeriod=artworksInPeriod,
                               browseExhibitions=browseExhibitions,
                               titleImage=titleImage,
                               form=form,
                               dateFrom = exDateFrom,
                               dateTo=exDateTo,
                               )




