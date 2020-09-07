from requests_html import HTMLSession
import urllib.request
import os
import connector
session = HTMLSession()

def pcgScrap(pageUrl, scrapedWebsite):

    ng = session.get(pageUrl)

    # IF FINDS ITEM'S NAME, IT CONTINUES

    checkArtworkPage = ng.html.find('.breadcrumbs', first=True) # Search for breadcrumbs and if there are, it continues

    if not checkArtworkPage == None:

        artworkData = {}

        # SCRAPPING ITEM NAME

        itemName = ng.html.find('h1', first=True)
        if not itemName == None:
            itemName = itemName.text
            titleStart = itemName.find(':')+2 # searches for ':' for finding the start of title
            artworkData['title'] = ''.join(list(itemName)[titleStart:])  # cut all letters before titleStart

        # SCRAPPING AUTHOR

        author = ng.html.find('h1', first=True)
        if not author == None:
            author = author.text
            authorEnd = author.find(':')  # searches for ':' for finding the end of author
            artworkData['author'] = [''.join(list(author)[:authorEnd])] # cut all letters after authorEnd

        # SCRAPPING CREATION DATE

        creationDate = ng.html.find('#page-content', first=True)
        if not creationDate == None:
            creationDate = creationDate.text
            creationDateStart = creationDate.find('datace:') + 8
            creationDateEnd = creationDate.find('\ntechnika:')
            artworkData['dating'] = ''.join(list(creationDate)[creationDateStart:creationDateEnd])  # cut all letters before creationDateStart and after creationDateEnd

        # SCRAPPING MATERIAL

        material = ng.html.find('#page-content', first=True)
        if not material == None:
            material = material.text
            materialStart = creationDate.find('materiál') + 10
            if material.find('\ndalší díla umělce') != -1: # if page contains 'dalsi dila umelce' it sets materialEnd by its start
                materialEnd = material.find('\ndalší díla umělce') -2
            else:
                materialEnd = material.find('\n\n$(function ()')
            artworkData['medium'] = ''.join(list(material)[materialStart:materialEnd])  # cut all letters before xStart and after xEnd

        # SCRAPPING TECHNIQUE

        technique = ng.html.find('#page-content', first=True)
        if not technique == None:
            technique = technique.text
            techniqueStart = technique.find('technika:') + 10
            techniqueEnd = technique.find('\nmateriál:')
            artworkData['work_type'] = ''.join(list(technique)[techniqueStart:techniqueEnd])  # cut all letters before xStart and after xEnd

        # SCRAPPING ORIGINAL ID

        inventoryId = ng.html.find('#page-content', first=True)
        if not inventoryId == None:
            inventoryId = inventoryId.text
            inventoryIdStart = inventoryId.find('inv. č.:') + 9
            inventoryIdEnd = inventoryId.find('\n\nsbírka:')
            artworkData['original_id'] = ''.join(list(technique)[inventoryIdStart:inventoryIdEnd])  # cut all letters before xStart and after xEnd

        # ADDING DIGITAL CURATOR ID

        collectionShortcut = 'PCG'
        dcId = collectionShortcut + '-' + artworkData['original_id'].replace(" ", "")
        artworkData['id'] = dcId

        # ADDING COLLECTION

        artworkData['gallery'] = 'Prague City Gallery'
        collectionShortcut = 'PCG'

        # SAVING URL

        artworkData['gallery_url'] = pageUrl

        # SCRAPPING IMAGE

        def dlJpg(iiUrl, filePath, ngKey):
            imagePath = 'temp/' + filePath + ngKey + '.jpg'
            artworkData['image_id'] = ngKey + '.jpg'
            urllib.request.urlretrieve(iiUrl, imagePath)

        iiUrl = ng.html.find('.active-zoom-image', first=True)
        if iiUrl != None and 'no-image' not in str(iiUrl):  # if image exists and its name doesn't contain 'no-image'
            iiUrl = iiUrl.attrs
            iiUrl = iiUrl.get("src")  # takes value of src attribute
            iiUrl = scrapedWebsite + iiUrl
            print(iiUrl)
            dlJpg(iiUrl, '/', dcId)

        # OUTPUT

        print(artworkData)
        return artworkData

    else:
        print('Nothing here')

def scrapPcg():

    # SETTING INPUTS

    subcollectionId = input('Insert subcollection signature (Ex: CZK:US.K-): ') or 'CZK:US.K-'
    startUrlNumber = int(input('Insert first ID for scrapping: ') or 1)
    endUrlNumber = int(input('Insert last ID for scrapping: ') or 20)
    webUrl = 'http://ghmp.cz'
    collectionUrl = webUrl + '/online-sbirky/detail/' + subcollectionId

    # STARTING LOOP

    while startUrlNumber < endUrlNumber:
        startUrlNumber += 1
        pageUrl = str(collectionUrl) + str(startUrlNumber)
        print('Searching at: ' + str(pageUrl)+ ' ...')
        artwork = pcgScrap(pageUrl, webUrl)


        # IF ARTWORK CONTAINS IMAGE IT CALLS FUNCTIONS FOR WRITING TO THE ELASTIC AND SAVING IMAGE TO THE STORAGE

        if not artwork == None and 'image_id' in artwork:
            connector.uploadToStorage('artworks-all/' + artwork['image_id'], 'temp/' + artwork['image_id']) # saving image to google storage
            os.remove('temp/' + artwork['image_id']) # deleting temporary image from local
            dcId = artwork['id'] # Taking id from dic. WritetoElastic sends id separately
            del artwork['id'] # Deleting id
            documentData = {
                "doc": artwork,
                "doc_as_upsert": True
            }
            print('Artwork found: ', dcId, documentData)
            connector.writeToElastic(dcId, documentData) # saving data to Elastic

scrapPcg()
