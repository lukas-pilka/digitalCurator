from connector import writeToElastic
import json
import config
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import os
import time
from PIL import Image
from datetime import datetime


# PREPARING QUERY TO ELASTICSEARCH

queryConditions = [

        {
          "bool": {
            "should": config.supportedWorkTypes
          }
        }
      ]


# SET PART OF QUERY CONDITION WITH RULES FOR RESNET V2 API
resnetApiSwitch = input('Use Tensor Flow Resnet V2 detection? y/n:')
if resnetApiSwitch =='y':
    resnetTimeTreshold = input('Set time threshold for Resnet V2 in format "2023-01-01T23:59:00Z". All artworks with an older update time will be selected:') or '2000-01-01T23:59:00Z'
    queryConditions.append(
        {
          "bool": {
            "should": [
                {"bool": {"must_not": {"exists": {"field": "resnet_v2_motifs_updated"}}}},
                {"range": {"resnet_v2_motifs_updated": {"lte": resnetTimeTreshold}}},
            ]
          }
        },
    )

# SET PART OF QUERY CONDITION WITH RULES FOR GOOGLE ICONOGRAPHY API
iconographyApiSwitch = input('Use Google Vision Iconography detection? y/n:')
if iconographyApiSwitch == 'y':
    iconographyTimeTreshold = input('Set time threshold for Google Iconography in format "2023-01-01T23:59:00Z". All artworks with an older update time will be selected:') or '2000-01-01T23:59:00Z'
    queryConditions.append(
        {
            "bool": {
                "should": [
                    {"bool": {"must_not": {"exists": {"field": "iconography_motifs_updated"}}}},
                    {"range": {"iconography_motifs_updated": {"lte": iconographyTimeTreshold}}}
                ]
            }
        },
    )


# COMPLETING QUERY
query = {
  "query": {
    "bool": {
      "must": queryConditions
    }
  }
}
payload = {'size': 10000}

# TENSOR FLOW API

if resnetApiSwitch == 'y':
    print('Connecting to Tensor Flow Resnet V2 API...')

    # Imports for running inference on the TF-Hub module.
    import tensorflow as tf
    import tensorflow_hub as hub

    # Apply module
    module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1" #@param ["https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1", "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"]
    detector = hub.load(module_handle).signatures['default']

def resnetMotifsDetection(imageFile):
    # For downloading the image.
    import tempfile
    from PIL import Image
    from PIL import ImageOps

    # Download and resize image

    def download_and_resize_image(loadedImage):
        _, filename = tempfile.mkstemp(suffix=".jpg")
        pil_image = loadedImage
        new_width, new_height = pil_image.size
        pil_image = ImageOps.fit(pil_image, (new_width, new_height), Image.ANTIALIAS)
        pil_image_rgb = pil_image.convert("RGB")
        pil_image_rgb.save(filename, format="JPEG", quality=90)
        return filename

    def load_img(path):
        img = tf.io.read_file(path)
        img = tf.image.decode_jpeg(img, channels=3)
        return img

    def run_detector(detector, path):
        img = load_img(path)
        converted_img = tf.image.convert_image_dtype(img, tf.float32)[tf.newaxis, ...]
        start_time = time.time()
        result = detector(converted_img)
        end_time = time.time()
        result = {key: value.numpy() for key, value in result.items()}
        detectedMotifs = []
        minScore = 0.25  # using for selecting motifs with higher probability than minScore 0.5 = 50%
        for detectedMotif in range(len(result["detection_scores"])):
            if result["detection_scores"][detectedMotif].item() > minScore:
                detectedMotifs.append({'object': result["detection_class_entities"][detectedMotif].decode("utf-8"),
                                       'score': result["detection_scores"][detectedMotif].item(),
                                       'boundBox': result["detection_boxes"][detectedMotif].tolist(),
                                       'detector': 'Resnet V2',
                                       })
        print("Found %d motifs." % len(detectedMotifs))
        print("Inference time: ", end_time - start_time)
        return detectedMotifs

    # Perform inference
    print('Exploring image motifs with Tensor Flow version ' + str(tf.__version__))
    image_path = download_and_resize_image(imageFile)
    resnetDetectedMotifs = run_detector(detector, image_path)
    print(resnetDetectedMotifs)
    return resnetDetectedMotifs


# GOOGLE VISION ICONOGRAPHY

if iconographyApiSwitch == 'y':
    print('Connecting to Google Vision Iconography API')

    from google.cloud import automl
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="../"+config.googleCredentialsKey
    project_id = "tfcurator"
    model_id = "IOD6098856858854883328"

def iconographyMotifsDetection(imageFile):
    start_time = time.time()
    file_path = imageFile
    prediction_client = automl.PredictionServiceClient()

    # Get the full path of the model.
    model_full_id = automl.AutoMlClient.model_path(project_id, "us-central1", model_id)

    # Read the file.
    with open(file_path, "rb") as content_file:
        content = content_file.read()

    image = automl.Image(image_bytes=content)
    payload = automl.ExamplePayload(image=image)

    # params is additional domain-specific parameters.
    # score_threshold is used to filter the result
    # https://cloud.google.com/automl/docs/reference/rpc/google.cloud.automl.v1#predictrequest
    params = {"score_threshold": "0.25"}

    request = automl.PredictRequest(name=model_full_id, payload=payload, params=params)
    response = prediction_client.predict(request=request)

    def run_detector():
        result = response.payload
        detectedMotifs = []
        minScore = 0.25  # using for selecting motifs with higher probability than minScore 0.25 = 25%
        for detectedMotif in result:
            boundBox = [
                detectedMotif.image_object_detection.bounding_box.normalized_vertices[0].y,
                detectedMotif.image_object_detection.bounding_box.normalized_vertices[0].x,
                detectedMotif.image_object_detection.bounding_box.normalized_vertices[1].y,
                detectedMotif.image_object_detection.bounding_box.normalized_vertices[1].x,
            ]
            motifName = detectedMotif.display_name.capitalize().replace("_"," ")  # Modifies the form of the word to be same as from Tensorflow
            if detectedMotif.image_object_detection.score > minScore:
                detectedMotifs.append({'object': motifName,
                                        'score': detectedMotif.image_object_detection.score,
                                        'boundBox': boundBox,
                                        'detector': 'Iconography',
                                        })
        print("Found %d motifs." % len(detectedMotifs))
        end_time = time.time()
        print("Inference time: ", end_time - start_time)
        return detectedMotifs

    print('Exploring image objects with Google Cloud Vision')
    iconographyDetectedMotifs = run_detector()
    print(iconographyDetectedMotifs)
    return iconographyDetectedMotifs



# RUN DETECTION FUNCTION DEFINITION

def runDetection():
    counter = 0

    # Downloading artworks from Elastic with a query prepared above
    print('Connecting to Elastic Search...')
    rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks3/_search',auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
    rawData.encoding = 'utf-8'
    dataDict = json.loads(rawData.text)
    artworks = dataDict['hits']['hits']

    # Printing count of artworks in Elastic without detected objects
    if len(artworks) >= 10000:
        print('More than 10 000 artworks for motif detection.')
    else:
        print(str(len(artworks)) + ' artworks for motif detection.')

    # Iterating threw artworks list and calling motifs detectors
    for artwork in artworks:
        print('artwork '+ str(counter))
        now = datetime.now()
        now = now.strftime("%Y-%m-%dT%H:%M:%SZ") # preparing time in elastic format
        print(now)

        try:
            imageUrl = 'https://storage.googleapis.com/tfcurator-artworks/artworks-all/'+artwork['_id']+'.jpg' # Creating img url from artwork id
            imageFileName = 'temp/'+artwork['_id']+'.jpg' # Creating image file name from artwork id
            urllib.request.urlretrieve(imageUrl, imageFileName) # Downloading image from url and saving to file name
            pilImage = Image.open(imageFileName)  # Converting to PIL image file
            print(imageUrl)

            # load current detected motifs or create new
            if 'detected_motifs' in artwork['_source']:
                detectedMotifs = artwork['_source']['detected_motifs']
            else:
                detectedMotifs = []

            # call TF Resnet and Google Iconography API by user selection in inputs
            if resnetApiSwitch == 'y':
                # It removes detected motifs with Resnet V2 detector which have been detected in the past
                detectedMotifs = [motif for motif in detectedMotifs if motif['detector'] != 'Resnet V2']
                # It calls detector and it adds newly detected motifs
                detectedMotifs += resnetMotifsDetection(pilImage)
            if iconographyApiSwitch == 'y':
                # It removes detected motifs with Iconography detector which have been detected in the past
                detectedMotifs = [motif for motif in detectedMotifs if motif['detector'] != 'Iconography']
                # It calls detector and it adds newly detected motifs
                detectedMotifs += iconographyMotifsDetection(imageFileName)

            # Preparing json for upload and calling Tensor Flow Resnet object detection

            documentData = {
                "doc": {
                    "detected_motifs": detectedMotifs
                },
                "doc_as_upsert": True
            }
            if resnetApiSwitch == 'y':
                documentData['doc']["resnet_v2_motifs_updated"] = now
            if iconographyApiSwitch == 'y':
                documentData['doc']["iconography_motifs_updated"] = now

            print('Detected motifs at '+ imageUrl +' :' + str(documentData))
            writeToElastic(artwork['_id'], documentData) # Writing to Digital Curator Elastic Search DB
            os.remove(imageFileName) # Removing image
        except Exception as e:
            print("type error: " + str(e))
            pass

        counter += 1
        print('----------')
    return len(artworks)

# CALLING RUN DETECTION

# Each round should detect and write motifs for 10 000 artworks
for i in range(50):
    notDetectedArtworks = runDetection()
    if notDetectedArtworks > 100:
        break




