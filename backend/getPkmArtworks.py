import csv
from requests_html import HTMLSession
import urllib.request
import connector
import os
import time
session = HTMLSession()

def pkmScrap(pageUrl):

    r = session.get(pageUrl)

    # IF FINDS ITEM'S NAME, IT CONTINUES

    checkArtworkPage = r.html.find('.artwork__title', first=True)  # Search for artwork__title and if there are, it continues

    if not checkArtworkPage == None:
        artworkData = {}

        # SCRAPPING ITEM NAME

        itemName = r.html.find('.artwork__title', first=True)
        if not itemName == None:
            itemName = itemName.text
            artworkData['title'] = itemName

        # SCRAPPING AUTHOR

        authorRawList = r.html.find('.content__item', containing='Artist')
        authorCell = authorRawList[2].text # selects 3rd cell containing text string (because 2 more exists)
        authorStart = authorCell.find('\n')+1  # searches for line break for finding the start of author name
        artworkData['author'] = [''.join(list(authorCell)[authorStart:])]  # cut all letters before authorStart

        # SCRAPPING CREATION DATE
        datingCell = r.html.find('.content__item', containing='Dating', first=True)
        datingCell = datingCell.text
        datingStart = datingCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['dating'] = ''.join(list(datingCell)[datingStart:])  # cut all letters before value start

        # SCRAPPING MAEDIUM
        materialCell = r.html.find('.content__item', containing='Material / Technology / Carrier', first=True)
        materialCell = materialCell.text
        materialStart = materialCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['medium'] = ''.join(list(materialCell)[materialStart:])  # cut all letters before value start

        # SCRAPPING WORK TYPE
        workTypeCell = r.html.find('.content__item', containing='genre', first=True)
        workTypeCell = workTypeCell.text
        workTypeStart = workTypeCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['work_type'] = ''.join(list(workTypeCell)[workTypeStart:])  # cut all letters before value start

        # SCRAPPING MEASUREMENT
        measurementCell = r.html.find('.content__item', containing='Dimensions of the object', first=True)
        measurementCell = measurementCell.text
        measurementStart = measurementCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['measurement'] = ''.join(list(measurementCell)[measurementStart:])  # cut all letters before value start

        # SCRAPPING GALLERY
        galleryCell = r.html.find('.content__item', containing='Stock', first=True)
        galleryCell = galleryCell.text
        galleryStart = galleryCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['gallery'] = ''.join(list(galleryCell)[galleryStart:])  # cut all letters before value start

        # SCRAPPING DESCRIPTION
        try:
            descriptionCell = r.html.find('.content__item', containing='More about this artwork', first=True)
            descriptionCell = descriptionCell.text
            descriptionStart = descriptionCell.find('\n') + 1  # searches for line break for finding the start of requested value
            artworkData['description'] = ''.join(list(descriptionCell)[descriptionStart:])  # cut all letters before value start
        except:
            pass

        # SCRAPPING ORIGINAL ID
        originalIdCell = r.html.find('.content__item', containing='Inventory number', first=True)
        originalIdCell = originalIdCell.text
        originalIdStart = originalIdCell.find('\n') + 1  # searches for line break for finding the start of requested value
        artworkData['original_id'] = ''.join(list(originalIdCell)[originalIdStart:])  # cut all letters before value start

        # ADDING DIGITAL CURATOR ID
        collectionShortcut = 'PKM'
        dcId = collectionShortcut + '-' + artworkData['original_id'].replace(" ", "")
        artworkData['id'] = dcId

        # SAVING URL
        artworkData['gallery_url'] = pageUrl

        # ADDING LICENCE
        artworkData['is_free'] = True
        artworkData['licence'] = 'CC BY-SA 4.0'

        # SCRAPPING IMAGE
        def dlJpg(iiUrl, filePath, dcId):
            imagePath = 'temp' + filePath + dcId + '.jpg'
            artworkData['image_id'] = dcId + '.jpg'
            urllib.request.urlretrieve(iiUrl, imagePath)

        iiUrl = r.html.find('.artwork__image img', first=True)
        if iiUrl != None and 'placeholder' not in str(iiUrl):  # if image exists and its name doesn't contain 'placeholder'
            iiUrl = iiUrl.attrs
            iiUrl = iiUrl.get("src")  # takes value of src attribute
            dlJpg(iiUrl, '/', dcId)

        return artworkData

    else:
        print('nothing here')



def scrapPkm():

    # LOADING URLs FROM CSV
    pkmLinks = []
    with open('pkmLinks.csv', newline='') as csvfile:
        csvLinks = csv.reader(csvfile, delimiter=',')
        for row in csvLinks:
            pkmLinks.append(', '.join(row))

    # STARTING LOOP
    for pageUrl in pkmLinks:
        print('Searching at: ' + str(pageUrl) + ' ...')
        artwork = pkmScrap(pageUrl)
        print(artwork)

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

            time.sleep(3)

scrapPkm()

