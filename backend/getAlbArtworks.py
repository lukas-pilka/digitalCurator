from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os
import connector

from requests_html import HTMLSession
import time
from datetime import datetime
import urllib.request
from backend.clearDate import setDateRange


def getArtworkData(pageUrl):

    # GET SOURCE CODE

    try:
        options = Options()
        options.headless = True
        options.add_argument("--window-size=1920,1200")
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(pageUrl)
        time.sleep(2)

        title = driver.find_element(By.CLASS_NAME, "recordViewRecordTitle").text
        recordView = driver.find_element(By.ID, "ccContents").text
        imageUrl = driver.find_element(By.ID, "recordViewImage").get_attribute("src")

        artworkData = {}

        # TITLE
        if len(title) > 0:
            artworkData['title'] = title

        # AUTHOR
        authorStart = recordView.find('\nKünstler_in\n')
        if authorStart > -1:
            authorStart += 13
            authorLength = recordView[authorStart:].find('\n')
            authorEnd = authorStart + authorLength
            author = recordView[authorStart:authorEnd]
        else:
            author = "Anonym"

        # If the author is anonymous and "After author" is mentioned
        if author == "Anonym" and recordView.find('\nNach\n') > -1:
            nachStart = recordView.find('\nNach\n') + 6
            nachLength = recordView[nachStart:].find('\n')
            nachEnd = nachStart + nachLength
            author = "After " + recordView[nachStart:nachEnd]

        # If the author is anonymous and "credited" is mentioned
        if author == "Anonym" and recordView.find('\nZugeschrieben an\n'):
            creditedStart = recordView.find('\nZugeschrieben an\n')
            if creditedStart > -1:
                creditedStart += 18
                creditedLength = recordView[creditedStart:].find('\n')
                creditedEnd = creditedStart + creditedLength
                author = recordView[creditedStart:creditedEnd]

        # If the author is anonymous and "workshop" is mentioned
        if author == "Anonym" and recordView.find('\nWerkstatt\n'):
            workshopStart = recordView.find('\nWerkstatt\n')
            if workshopStart > -1:
                workshopStart += 11
                workshopLength = recordView[workshopStart:].find('\n')
                workshopEnd = workshopStart + workshopLength
                author = "Workshop of " + recordView[workshopStart:workshopEnd]

        # If the author is anonymous and "workshop" is mentioned
        if author == "Anonym" and recordView.find('\nUmkreis\n'):
            circleStart = recordView.find('\nUmkreis\n')
            if circleStart > -1:
                circleStart += 9
                circleLength = recordView[circleStart:].find('\n')
                circleEnd = circleStart + circleLength
                author = "Circle of " + recordView[circleStart:circleEnd]

        artworkData['author'] = author

        # DATING
        datingStart = recordView.find('\nDatierung\n')
        if datingStart > -1:
            datingStart += 11
            datingLength = recordView[datingStart:].find('\n')
            datingEnd = datingStart + datingLength
            dating = recordView[datingStart:datingEnd]
            artworkData['dating'] = dating

        artworkData = setDateRange(artworkData) # If dating can be decoded, it extends input dict by adding date_earliest and date_latest

        # WORK TYPE
        workTypeStart = recordView.find('\nTechnik\n')
        if workTypeStart > -1:
            workTypeStart += 9
            workTypeLength = recordView[workTypeStart:].find('\n')
            workTypeEnd = workTypeStart + workTypeLength
            workType = recordView[workTypeStart:workTypeEnd]
            artworkData['work_type'] = workType

        # MEASUREMENT
        measurementStart = recordView.find('\nMaße\n')
        if measurementStart > -1:
            measurementStart += 9
            measurementLength = recordView[measurementStart:].find('\n')
            measurementEnd = measurementStart + measurementLength
            measurement = recordView[measurementStart:measurementEnd]
            artworkData['measurement'] = measurement

        # ORIGINAL ID
        originaIdStart = recordView.find('\nInventarnummer\n')
        if originaIdStart > -1:
            originaIdStart += 16
            originaIdLength = recordView[originaIdStart:].find('\n')
            originaIdEnd = originaIdStart + originaIdLength
            originaId = recordView[originaIdStart:originaIdEnd]
            artworkData['original_id'] = originaId

        # CREATED AT
        artworkData['created_at'] = datetime.now().strftime("%Y-%m-%d, %H:%M:%S")

        # GALLERY
        artworkData['gallery'] = 'Albertina Wien'

        # GALLERY URL
        artworkData['gallery_url'] = pageUrl

        # LICENCE
        artworkData['is_free'] = True
        artworkData['licence'] = 'iiif'

        # DIGITAL CURATOR ID
        collectionShortcut = 'ALB'
        dcId = collectionShortcut + '-' + artworkData['original_id'].replace("/", "-").replace(' ', '-')
        artworkData['id'] = dcId

        # DOWNLOADING IMAGE
        if imageUrl != None and 'nondisponible' not in str(imageUrl):  # if image exists and its name doesn't contain 'no-image'
            imagePath = 'temp/' + artworkData['id'] + '.jpg'
            artworkData['image_id'] = artworkData['id'] + '.jpg'
            urllib.request.urlretrieve(imageUrl, imagePath)

        # OUTPUT
        if 'image_id' in artworkData.keys() and 'title' in artworkData.keys():
            print(artworkData)
            return artworkData
        else:
            print('No image here :(')

    except Exception as e:
        print('An error occured')
        # print(e)
        time.sleep(3)

    driver.quit()


def scrapAlb():

    # SETTING INPUTS
    startYear = int(input('Insert first year for scrapping: ') or 1900)
    startUrlNumber = int(input('Insert first ID for scrapping: ') or 1)
    endUrlNumber = int(input('Insert last ID for scrapping: ') or 10000)
    webUrl = 'https://sammlungenonline.albertina.at'
    failedSeries = 0
    failedSeriesLimit = 100

    # STARTING LOOP

    while startUrlNumber < endUrlNumber:
        startUrlNumber += 1
        pageUrl = webUrl + '/?query=search=/record/objectnumbersearch=%5B' + str(startYear) + '/' + str(startUrlNumber) + '%5D&showtype=record'
        print('Searching at: ' + str(pageUrl) + ' ...')
        artwork = getArtworkData(pageUrl)

        # CHECK IF THERE ARE TOO MANY FAILED ATTEMPTS IN A ROW

        if artwork == None:
            failedSeries += 1
            print('Failed attempt, ' + str(failedSeries) + ' in row')
            if failedSeries > failedSeriesLimit: # If too many failed attempts, it skip to next year
                startYear += 1
                failedSeries = 0
                startUrlNumber = 0
                print( 'Failed series limit reached, skip to next year: ' + str(startYear))


        # IF ARTWORK CONTAINS IMAGE IT CALLS FUNCTIONS FOR WRITING TO THE FIRESTORE AND SAVING IMAGE TO THE STORAGE

        if not artwork == None and 'image_id' in artwork:
            failedSeries = 0
            connector.uploadToStorage('artworks-all/' + artwork['image_id'], 'temp/' + artwork['image_id']) # saving image to google storage
            os.remove('temp/' + artwork['image_id']) # deleting temporary image from local
            dcId = artwork['id'] # Taking id from dic. WritetoElastic sends id separately
            del artwork['id'] # Deleting id
            documentData = {
                "doc": artwork,
                "doc_as_upsert": True
            }
            connector.writeToElastic(dcId, documentData) # saving data to Elastic

        print('---')

scrapAlb()


