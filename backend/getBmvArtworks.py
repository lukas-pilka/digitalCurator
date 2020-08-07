# IMPORTS

import os
import connector

from requests_html import HTMLSession
import urllib.request
session = HTMLSession()


def bmvScrap(pageUrl, scrapedWebsite):

        scraping = session.get(pageUrl)

        # IF FINDS ITEM NAME, IT CONTINUES

        checkArtworkPage = scraping.html.find('.detail-item-details', first=True)  # Search for element with class and if there is, it continues

        if not checkArtworkPage == None:

            artworkData = {}

            # SCRAPPING TITLE

            itemName = scraping.html.find('h1', first=True)
            if not itemName == None:
                artworkData['title'] = itemName.text

            # SCRAPPING AUTHOR

            author = scraping.html.find('.peopleField .detailFieldValue a', first=True)
            if not author == None:
                artworkData['author'] = [author.text]

            # SCRAPPING CREATION DATING

            creationDate = scraping.html.find('.displayDateField .detailFieldValue', first=True)
            if not creationDate == None:
                artworkData['dating'] = creationDate.text

            # ACQUISITION DATE

            acquisitionDate = scraping.html.find('.paperSupportField .detailFieldValue', first=True)
            if not acquisitionDate == None:
                artworkData['acquisition_date'] = acquisitionDate.text

            # SCRAPPING WORK TYPE

            technique = scraping.html.find('.nameField .detailFieldValue a', first=True)
            if not technique == None:
                artworkData['work_type'] = technique.text

            # SCRAPPING MEDIUM

            medium = scraping.html.find('.mediumField .detailFieldValue', first=True)
            if not medium == None:
                artworkData['medium'] = medium.text

            # SCRAPPING STYLE

            style = scraping.html.find('.periodField .detailFieldValue', first=True)
            if not style == None:
                artworkData['style'] = style.text

            # SCRAPPING SIGNATURE

            signature = scraping.html.find('.signedField .detailFieldValue', first=True)
            if not signature == None:
                artworkData['artist_signature'] = signature.text

            # SCRAPPING MEASUREMENT

            measurement = scraping.html.find('.dimensionsField .detailFieldValue', first=True)
            if not measurement == None:
                artworkData['measurement'] = measurement.text

            # SCRAPPING ORIGINAL ID

            originalId = scraping.html.find('.invnoField .detailFieldValue', first=True)
            if not originalId == None:
                artworkData['original_id'] = originalId.text

            # ADDING DIGITAL CURATOR ID

            collectionShortcut = 'BMV'
            dcId = collectionShortcut + '-' + artworkData['original_id'].replace("/", "-")
            artworkData['id'] = dcId

            # ADDING COLLECTION

            artworkData['gallery'] = 'Belvedere Museum Vienna'

            # SAVING URL

            artworkData['gallery_url'] = pageUrl

            # ADDING LICENCE

            artworkData['is_free'] = True
            artworkData['licence'] = 'iiif'

            # SCRAPPING IMAGE

            def dlJpg(iiUrl, filePath, ngKey):
                imagePath = 'temp' + filePath + ngKey + '.jpg'
                artworkData['image_id'] = ngKey + '.jpg'
                urllib.request.urlretrieve(iiUrl, imagePath)

            iiUrl = scraping.html.find('.width-img-wrap img', first=True)
            if iiUrl != None and 'no-image' not in str(iiUrl):  # if image exists and its name doesn't contain 'no-image'
                iiUrl = iiUrl.attrs
                iiUrl = iiUrl.get("src")  # takes value of src attribute
                iiUrlCut = iiUrl.find('/preview') # finds place where to cut url
                iiUrl = ''.join(list(iiUrl)[:iiUrlCut]) + '/full' # cuts url and adds ending
                iiUrl = scrapedWebsite + iiUrl
                print(iiUrl)
                dlJpg(iiUrl, '/', dcId)

            # OUTPUT

            print(artworkData)
            return artworkData

        else:
            print('Nothing here')

def scrapBmv():

    # SETTING INPUTS

    startUrlNumber = int(input('Insert first ID for scrapping: ') or 1)
    endUrlNumber = int(input('Insert last ID for scrapping: ') or 50)
    webUrl = 'https://sammlung.belvedere.at'
    collectionUrl = webUrl + '/objects/'

    # STARTING LOOP

    while startUrlNumber < endUrlNumber:
        startUrlNumber += 1
        pageUrl = str(collectionUrl) + str(startUrlNumber)
        print('Searching at: ' + str(pageUrl) + ' ...')
        artwork = bmvScrap(pageUrl, webUrl)

        # IF ARTWORK CONTAINS IMAGE IT CALLS FUNCTIONS FOR WRITING TO THE FIRESTORE AND SAVING IMAGE TO THE STORAGE

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


scrapBmv()
