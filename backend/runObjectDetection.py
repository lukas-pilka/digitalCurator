from connector import writeToElastic
import json
import config
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import os
from PIL import Image
from datetime import datetime


'''
# TEST OBJECT DETECTION ON LOCAL IMAGES
print(tfObjectDetection(Image.open('temp/WU-SVK-GMB-C-411.jpg')))
print(tfObjectDetection(Image.open('temp/WU-SVK-GMB-C-4260.jpg')))
print(tfObjectDetection(Image.open('temp/WU-CZE-4RG-O0090.jpg')))
print(tfObjectDetection(Image.open('temp/WU-CZE-4RG-K1320.jpg')))
'''


# CONNECTION TO ELASTIC SEARCH
lastTimeSwitch = input('Select artworks by previous object update. Set time in format 2000-01-01T23:59:00Z:') or '2022-01-01T23:59:00Z'
print('Connecting to Elastic Search...')

# Query returning artworks without detected objects
query = {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "should": [
                {"bool": {"must_not": {"exists": {"field": "detected_objects_updated"}}}},
                {"range": {"detected_objects_updated": {"gte": lastTimeSwitch}}}
            ]
          }
        },
        {
          "bool": {
            "should": [
              {"term": {"work_type": "graphic"}},
              {"term": {"work_type": "painting"}},
              {"term": {"work_type": "drawing"}}
            ]
          }
        }
      ]
    }
  }
}

payload = {'size': 10000}
rawData = requests.get('https://66f07727639d4755971f5173fb60e420.europe-west3.gcp.cloud.es.io:9243/artworks/_search',
                       auth=HTTPBasicAuth(config.userDcElastic, config.passDcElastic), params=payload, json=query)
rawData.encoding = 'utf-8'
dataDict = json.loads(rawData.text)
artworks = dataDict['hits']['hits']

# Printing count of artworks in Elastic without detected objects
if len(artworks) >= 10000:
    print('More than 10 000 artworks for object detection.')
else:
    print(str(len(artworks)) + ' artworks for object detection.')

# TENSOR FLOW API
tfApiSwitch = input('Use Tensor Flow object detection? y/n:')
if tfApiSwitch == 'y':
    print('Connecting to Tensor Flow API')

    # Imports for running inference on the TF-Hub module.
    import tensorflow as tf
    import tensorflow_hub as hub

    # Apply module
    module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1" #@param ["https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1", "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"]
    detector = hub.load(module_handle).signatures['default']

    def tfObjectDetection(imageFile):

        # For downloading the image.
        import tempfile
        from PIL import Image
        from PIL import ImageOps

        # For measuring the inference time.
        import time

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
            result = {key:value.numpy() for key,value in result.items()}

            print("Found %d objects." % len(result["detection_scores"]))
            print("Inference time: ", end_time-start_time)
            detectedObjects = []
            minScore = 0.1 # using for selecting objects with higher probability than minScore 0.1 = 10%
            for detectedObject in range(len(result["detection_scores"])):
                if result["detection_scores"][detectedObject].item() > minScore:
                    detectedObjects.append({'object': result["detection_class_entities"][detectedObject].decode("utf-8"),
                                       'score': result["detection_scores"][detectedObject].item(),
                                       'boundBox': result["detection_boxes"][detectedObject].tolist()
                    })
            return detectedObjects

        # Perform inference
        print('Exploring image objects with Tensor Flow version ' + str(tf.__version__))
        image_path = download_and_resize_image(imageFile)
        tfDetectedObjects = run_detector(detector, image_path)
        print(tfDetectedObjects)
        return tfDetectedObjects

# GOOGLE VISION API
googleApiSwitch = input('Use Google Vision object detection? y/n:')
if googleApiSwitch == 'y':
    print('Connecting to GOOGLE VISION API')

    from google.cloud import automl
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="../../keys/tfcurator-c227c8fe0180.json"
    project_id = "tfcurator"
    model_id = "IOD6455569217230995456"

    def googleObjectDetection(imageFile):

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
        params = {"score_threshold": "0.1"}

        request = automl.PredictRequest(name=model_full_id, payload=payload, params=params)
        response = prediction_client.predict(request=request)

        def run_detector():
            result = response.payload
            detectedObjects = []
            print("Found %d objects." % len(result))
            for detectedObject in result:
                boundBox = [
                    detectedObject.image_object_detection.bounding_box.normalized_vertices[0].y,
                    detectedObject.image_object_detection.bounding_box.normalized_vertices[0].x,
                    detectedObject.image_object_detection.bounding_box.normalized_vertices[1].y,
                    detectedObject.image_object_detection.bounding_box.normalized_vertices[1].x,
                ]
                objectName = detectedObject.display_name.capitalize().replace("_", " ") # Modifies the form of the word to be same as from Tensorflow
                detectedObjects.append({'object': objectName,
                                   'score': detectedObject.image_object_detection.score,
                                   'boundBox': boundBox
                                   })
            return detectedObjects

        print('Exploring image objects with Google Cloud Vision')
        googleDetectedObjects = run_detector()
        print(googleDetectedObjects)
        return googleDetectedObjects

# ITERATING THROUGH ARTWORK LIST
appendSwitch = input('Append or overwrite current objects? a = append, o = overwrite:')
counter = 0
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

        # load current detected object or overwrite it (by user selection in appendSwitch)

        if 'detected_objects' in artwork['_source'].keys() and appendSwitch == 'a':
            detectedObjects = artwork['_source']['detected_objects']
        else:
            detectedObjects = []

        # call TF and Google API by user selection in inputs

        if tfApiSwitch == 'y':
            detectedObjects += tfObjectDetection(pilImage)
        if googleApiSwitch == 'y':
            detectedObjects += googleObjectDetection(imageFileName)

        # Preparing json for upload and calling Tensor Flow object detection

        documentData = {
            "doc": {
                "detected_objects_updated": now,
                "detected_objects": detectedObjects
            },
            "doc_as_upsert": True
        }
        print('Detected objects: ' + str(documentData))
        writeToElastic(artwork['_id'], documentData) # Writing to Digital Curator Elastic Search DB
        print('Data recorded for: ' + imageUrl)
        os.remove(imageFileName) # Removing image
    except:
        print('An error occurred')
        pass

    counter += 1
    print('----------')



