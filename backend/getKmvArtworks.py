# IMPORTS

import os
import connector

from requests_html import HTMLSession
import urllib.request
session = HTMLSession()


def kmvScrap(pageUrl, scrapedWebsite):

        scraping = session.get(pageUrl)
        scraping.html.render()
        ogDescription = scraping.html.xpath("//meta[@property='og:description']/@content")[0].split(", ")

        # IF FINDS ITEM NAME, IT CONTINUES

        checkArtworkPage = scraping.html.find('.object-description-section', first=True)  # Search for element with class and if there is, it continues

        if not checkArtworkPage == None:

            artworkData = {}

            # SCRAPPING TITLE

            itemName = scraping.html.find('h1', first=True).text
            if not itemName == None:
                artworkData['title'] = itemName
            
            # ADDING AUTHOR

            if 'Artist:' in ogDescription[1]:
                artworkData['author'] = ogDescription[1][7:]
            elif 'Attributed to:' in ogDescription[1]:
                artworkData['author'] = ogDescription[1][14:]

            # ADDING CREATION DATING

            artworkData['dating'] = ogDescription[0]

            # SCRAPPING WORK TYPE

            workTypeRaw = scraping.html.find('.object-description-section', first=True).text
            if not workTypeRaw == None:
                workTypeStart = workTypeRaw .find('\nObject Name\n') + 13
                workTypeLength = workTypeRaw [workTypeStart:].find('\nCulture\n')
                workTyperEnd = workTypeStart + workTypeLength
                workType = workTypeRaw[workTypeStart:workTyperEnd]
                artworkData['work_type'] = workType

            # ADDING ORIGINAL ID

            artworkData['original_id'] = pageUrl[38:]

            # ADDING DIGITAL CURATOR ID

            collectionShortcut = 'KMV'
            dcId = collectionShortcut + '-' + artworkData['original_id'].replace("/", "-").replace(' ', '-')
            artworkData['id'] = dcId

            # ADDING COLLECTION

            artworkData['gallery'] = 'Kunsthistorisches Museum Vienna'
            
            # SAVING URL

            artworkData['gallery_url'] = pageUrl

            # ADDING LICENCE

            artworkData['is_free'] = False

            # SCRAPPING IMAGE

            def dlJpg(iiUrl, filePath, ngKey):
                imagePath = 'temp' + filePath + ngKey + '.jpg'
                artworkData['image_id'] = ngKey + '.jpg'
                urllib.request.urlretrieve(iiUrl, imagePath)

            iiUrl = scraping.html.xpath("//meta[@property='og:image']/@content")[0]

            if iiUrl != None and 'no-image' not in str(iiUrl):  # if image exists and its name doesn't contain 'no-image'
                dlJpg(iiUrl, '/', dcId)

            # OUTPUT

            return artworkData

        else:
            print('Nothing here')


def scrapKmv():

    # SETTING INPUTS

    startUrlNumber = int(input('Insert first ID for scrapping: ') or 100)
    endUrlNumber = int(input('Insert last ID for scrapping: ') or 130)
    webUrl = 'https://www.khm.at'
    collectionUrl = webUrl + '/en/objectdb/detail/'

    # STARTING LOOP

    while startUrlNumber < endUrlNumber:
        startUrlNumber += 1
        pageUrl = str(collectionUrl) + str(startUrlNumber)
        print('Searching at: ' + str(pageUrl) + ' ...')
        artwork = kmvScrap(pageUrl, webUrl)

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

        print('-----')


scrapKmv()
