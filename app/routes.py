# IMPORTS

import config
import engine
import time
from datetime import datetime

# Flask

from app import app
from flask import render_template, g, url_for, redirect, request
from flask_sitemap import Sitemap
ext = Sitemap(app=app)

# Forms
from .forms import SearchForm
app.config['SECRET_KEY'] = 'you-will-never-guess'

# Loads SearchForm from forms.py, pre-fills fields from arguments and sets default values
def buildSearchForm(receivedArguments={}):

    # The structure of the arguments can be different depending on whether it is a user query or an exhibition defined in config. This unifies it into a single level list.
    parsedArguments = []
    if 'exDisplayedObjects' in receivedArguments.keys():
        for motifsString in receivedArguments['exDisplayedObjects']:
            motifsList = motifsString.strip('][').split(', ')
            for motif in motifsList:
                parsedArguments.append(motif.strip("''"))

    form = SearchForm(
        searchedClassSelect=tuple(parsedArguments) if len(parsedArguments) > 0 else None,
        exhibitionName=receivedArguments['exName'][0] if 'exName' in receivedArguments.keys() else None,
        dateFrom=receivedArguments['exDateFrom'][0] if 'exDateFrom' in receivedArguments.keys() else 1300,
        dateTo=receivedArguments['exDateTo'][0] if 'exDateTo' in receivedArguments.keys() else 2020,
    )
    return form

# After form submit it posts values into url attributes and redirect to start
def formValidateOnSubmit(form):
    if len(form.exhibitionName.data) > 0:
        exName = form.exhibitionName.data
    else:
        exName = "Digital curator's choice"
    exDisplayedObjects = form.searchedClassSelect.data  # Loads list of classes from select multiple choices
    exComparisonObjects = form.comparisonClassSelect.data  # Loads list of classes from select multiple choices
    exDateFrom = form.dateFrom.data  # Loads exDateFrom from select
    exDateTo = form.dateTo.data  # Loads exDateTo from select
    url = url_for('exhibition', exName=exName, exDisplayedObjects=exDisplayedObjects,
                  exComparisonObjects=exComparisonObjects, exDateFrom=exDateFrom, exDateTo=exDateTo)
    return url

@app.before_request
def before_request():
    g.request_start_time = time.time()
    g.request_time = lambda: "%.5fs" % (time.time() - g.request_start_time)

@app.route('/', methods=['GET', 'POST'])
def intro():
    form = buildSearchForm()

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    return render_template('intro.html',
                           galleriesSum=engine.getGalleriesSum(),
                           museums=engine.getMuseums(),
                           form=form
                           )

# Returns exhibition
@app.route('/app', methods=['GET', 'POST'])
def exhibition():

    # Loads SearchForm from forms.py, pre-fills fields from arguments and sets default values
    receivedArguments = request.args.to_dict(flat=False)
    form = buildSearchForm(receivedArguments)

    # If it doesn't receive arguments it set arguments with default values of exhibition from config
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
        simpleObjectList = []  # Preparing simple list for decisions on displaying bound boxes (string compliance is required)
        for objectSet in exDisplayedObjects:
            for selectedObject in objectSet:
                simpleObjectList.append(selectedObject)
        exhibitionsList = [{set1Name: [displayedObject for displayedObject in exDisplayedObjects]}]

        # tests whether data comparison objects exists in arguments
        try:
            exComparisonObjectsNotParsed = request.args.getlist('exComparisonObjects')  # it returns strings instead of lists, parsing is necessary
            exComparisonObjects = [i.strip("[]").replace("'", "").split(', ') for i in exComparisonObjectsNotParsed]  # Parsing - geting lists from strings
            for objectSet in exComparisonObjects:
                for selectedObject in objectSet:
                    simpleObjectList.append(selectedObject)
            set2Name = engine.prepareName(sum(exComparisonObjects, []))
            exhibitionsList.append({set2Name: [comparisonObject for comparisonObject in exComparisonObjects]})
        except:
            pass

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    # Sending request to Elastic
    artworksInPeriod = engine.getPeriodData(exhibitionsList, exDateFrom, exDateTo)
    artworksSorted = engine.getArtworksByObject(exhibitionsList, exDateFrom, exDateTo)

    # Preparing links for related tags
    for artworkSet in artworksSorted:
        for artwork in artworkSet:
            engine.getRelatedTags(artwork)

    # Check for zero results
    if len(artworksSorted[0]) == 0:
        return render_template('index.html',
                               exName=exName,
                               galleriesSum=engine.getGalleriesSum(),
                               artworksInPeriod=artworksInPeriod,
                               galleryResultPage=True,
                               form=form,
                               )

    else:
        titleImage = artworksSorted[0][0]
        collectionsByPeriods = engine.sortCollectionByPeriods(artworksInPeriod, artworksSorted)
        collectionTitles = []  # Clearing because dicts between searched objects
        pageDescription = f"Digital Curator's exhibition displaying artworks with {artworksInPeriod['artworksWithObject'][0][0]} was assembled automatically by AI computer vision."

        for collection in exhibitionsList:
            collectionTitles.append(list(collection.keys())[0])
        return render_template('index.html',
                               exName=exName,
                               pageTitle=exName,
                               metaDescription=pageDescription,
                               artworksForWeb=collectionsByPeriods,
                               searchedObjects=collectionTitles,
                               galleriesSum=engine.getGalleriesSum(),
                               artworksInPeriod=artworksInPeriod,
                               titleImage=titleImage,
                               galleryResultPage=True,
                               form=form,
                               dateFrom = exDateFrom,
                               dateTo=exDateTo,
                               simpleObjectList=simpleObjectList,
                               )

# Browse exhibitions
@app.route('/browseexhibitions', methods=['GET', 'POST'])
def browseExhibitions():
    form = buildSearchForm()
    museums = engine.getMuseums()

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    return render_template('browseExhibitions.html',
                           galleriesSum=engine.getGalleriesSum(),
                           museums=museums,
                           browseExhibitions=engine.preparedExhibitions(),
                           form=form
                           )

# About project
@app.route('/aboutproject', methods=['GET', 'POST'])
def aboutProject():
    form = buildSearchForm()

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    return render_template('aboutProject.html',
                           galleriesSum=engine.getGalleriesSum(),
                           form=form
                           )

# Join us
@app.route('/joinus', methods=['GET', 'POST'])
def joinUs():
    form = buildSearchForm()

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    return render_template('joinUs.html',
                           galleriesSum=engine.getGalleriesSum(),
                           form=form
                           )

# Artwork detail
@app.route('/artwork/<artworkId>', methods=['GET', 'POST'])
def artworkDetail(artworkId):
    form = buildSearchForm()
    artwork = engine.getArtworkById(artworkId)
    relatedTags = engine.getRelatedTags(artwork)
    print(artwork)

    if 'description' in artwork['_source'].keys():
        pageDescription = artwork['_source']['description']
    else:
        pageDescription = f"{artwork['_source']['title']} by {artwork['_source']['author']}: Digitized artwork explored by computer vision."

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    # artworkId doesnt exist in database
    if engine.getArtworkById(artworkId) == False:
        return redirect('/page_not_found')

    return render_template('artworkDetail.html',
                           pageTitle=f"{artwork['_source']['author']} | {artwork['_source']['title']}",
                           pageDescription = pageDescription,
                           galleriesSum=engine.getGalleriesSum(),
                           form=form,
                           artwork=artwork,
                           titleImage=artwork,
                           relatedTags=relatedTags
                           )

# 404
@app.errorhandler(404)
def page_not_found(e):
    form = buildSearchForm()

    # form submit calls function defined above
    if form.validate_on_submit():
        url = formValidateOnSubmit(form)
        return redirect(url)

    return render_template('404.html',
                           galleriesSum=engine.getGalleriesSum(),
                           form=form
                           ), 404

# Flask Sitemap
@ext.register_generator
def index():
    yield 'intro', {}, datetime.now().date(), 'monthly', 1.0
    yield 'exhibition', {}, datetime.now().date(), 'monthly', 1.0
    yield 'browseExhibitions', {}, datetime.now().date(), 'monthly', 0.7
    yield 'aboutProject', {}, datetime.now().date(), 'monthly', 0.7
    yield 'joinUs', {}, datetime.now().date(), 'monthly', 0.7

    for id in engine.getAllIds():
        yield 'artworkDetail',{'artworkId':id}, datetime.now().date(), 'yearly', 0.5





