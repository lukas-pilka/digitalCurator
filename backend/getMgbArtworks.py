from requests_html import HTMLSession
import urllib
import os
import urllib.request
import connector
session = HTMLSession()

def mgbScrap(pageUrl, scrapedWebsite):

    ng = session.get(pageUrl)

    # IF FINDS ITEM'S NAME, IT CONTINUES

    ngItemName = ng.html.find('.nadpis-dielo', first=True)

    if not ngItemName == None:

        artworkData = {}

        # SCRAPPING ITEM NAME

        ngItemName = ng.html.find('.nadpis-dielo', first=True)
        if not ngItemName == None:
            artworkData['title'] = ngItemName.text

        # SCRAPPING AUTHOR

        ngAuthor = ng.html.find('.inline', first=True)
        if not ngAuthor == None:
            artworkData['author'] = ngAuthor.text

        # SCRAPPING CREATION DATE

        ngCreationDate = ng.html.find('tr', containing='datace:', first=True)
        if not ngCreationDate == None:
            artworkData['dating'] = ''.join(list(ngCreationDate.text)[8:]) # CUT X LETTERS FROM BEGINNING

        # SCRAPPING DIMENSIONS

        ngDimensions = ng.html.find('tr', containing='rozměry:', first=True)
        if not ngDimensions == None:
            artworkData['measurement'] = ''.join(list(ngDimensions.text)[9:]) # CUT X LETTERS FROM BEGINNING

        # SCRAPPING MATERIAL

        ngMaterial = ng.html.find('tr', containing='materiál:', first=True)
        if not ngMaterial == None:
            artworkData['medium'] = ''.join(list(ngMaterial.text)[10:]) # CUT X LETTERS FROM BEGINNING

        # SCRAPPING TECHNIQUE

        ngTechnique = ng.html.find('tr', containing='technika:', first=True)
        if not ngTechnique == None:
            artworkData['work_type'] = ''.join(list(ngTechnique.text)[10:]) # CUT X LETTERS FROM BEGINNING

        # SCRAPPING SIGNATURE

        ngSignature = ng.html.find('tr', containing='značení:', first=True)
        if not ngSignature == None:
            artworkData['artist_signature'] = ''.join(list(ngSignature.text)[9:]) # CUT X LETTERS FROM BEGINNING

        # SCRAPPING INVENTORY ID

        ngInventoryId = ng.html.find('tr', containing='inventární číslo:', first=True)
        if not ngInventoryId == None:
            ngInventoryId = ''.join(list(ngInventoryId.text)[18:]) # CUT X LETTERS FROM BEGINNING
            artworkData['original_id'] = ngInventoryId

        # ADDING LICENCE

        artworkData['is_free'] = False

        # SCRAPPING DESCRIPTION

        ngDescription = ng.html.find('.description', first=True)
        if not ngDescription == None:
            artworkData['description'] = ngDescription.text

        # ADDING COLLECTION

        artworkData['gallery'] = 'Moravian Gallery in Brno'


        # ADDING DIGITAL CURATOR ID
        collectionShortcut = 'MGB'
        dcId = collectionShortcut + '-' + artworkData['original_id'].replace(" ", "")
        artworkData['id'] = dcId

        # SAVING URL

        artworkData['gallery_url'] = pageUrl

        # SCRAPPING IMAGE

        def dlJpg(iiUrl, filePath, ngKey):
            imagePath = 'temp/' + filePath + ngKey + '.jpg'
            artworkData['image_id'] = ngKey + '.jpg'
            urllib.request.urlretrieve(iiUrl, imagePath)

        iiUrl = ng.html.find('.img-dielo', first=True)

        if iiUrl != None:
            iiUrl = iiUrl.attrs
            iiUrl = iiUrl.get("src")  # TAKES VALUE OF SRC ATTRIBUTE
            iiUrl = scrapedWebsite + iiUrl
            if iiUrl != 'https://sbirky.moravska-galerie.cz/images/mg/no-image.jpg': # Placeholder "no-image image check" check
                dlJpg(iiUrl, '/', dcId)
            else:
                print('No real image, just a placeholder')

        # OUTPUT

        return artworkData

    else:
        print('Nothing here')


def scrapMgb():

    # SETTING INPUTS

    '''

    CZE:MG.A_       6621
    CZE:MG.SDK_      889
    ZE:MG.MM_       2079
    CZE:MG.STD_     1000
    CZE:MG.C_      25241
    CZE:MG.SDR_     3163
    '''

    subcollectionId = input('Insert subcollection signature (Ex: CZE:MG.A_): ') or 'CZE:MG.A_'
    startUrlNumber = int(input('Insert first ID for scrapping: ') or 1)
    endUrlNumber = int(input('Insert last ID for scrapping: ') or 10)
    webUrl = 'https://sbirky.moravska-galerie.cz'
    collectionUrl = webUrl + '/dielo/' + subcollectionId

    # STARTING CYCLE

    while startUrlNumber < endUrlNumber:
        startUrlNumber += 1
        pageUrl = str(collectionUrl) + str(startUrlNumber)
        print('Searching at: ' + str(pageUrl)+ ' ...')
        artwork = mgbScrap(pageUrl, webUrl)

        # IF ARTWORK CONTAINS IMAGE IT CALLS FUNCTIONS FOR WRITING TO THE ELASTIC AND SAVING IMAGE TO THE STORAGE

        if not artwork == None and 'image_id' in artwork:
            connector.uploadToStorage('artworks-all/' + artwork['image_id'],
                                      'temp/' + artwork['image_id'])  # saving image to google storage

            os.remove('temp/' + artwork['image_id'])  # deleting temporary image from local
            dcId = artwork['id']  # Taking id from dic. WritetoElastic sends id separately
            del artwork['id']  # Deleting id
            documentData = {
                "doc": artwork,
                "doc_as_upsert": True
            }

            print('Artwork found: ', dcId, documentData)
            connector.writeToElastic(dcId, documentData)  # saving data to Elastic

        print('-------')

scrapMgb()