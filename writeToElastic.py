def writeToElastic(documentId, documentData):
    # IMPORTS

    import requests
    from requests.auth import HTTPBasicAuth
    import config

    # POST TO ELASTIC SEARCH

    payload = ''
    data = requests.post(
        'https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/item/' + documentId + '/_update',
        auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=documentData)
    print('Post successful!')




