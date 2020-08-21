from connector import writeToElastic
import json
import config
import requests
from requests.auth import HTTPBasicAuth
import urllib.request
import os
from PIL import Image

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
        boundBoxes = []
        minScore = 0.1 # using for selecting objects with higher probability than minScore 0.1 = 10%
        for detectedObject in range(len(result["detection_scores"])):
            if result["detection_scores"][detectedObject].item() > minScore:
                boundBoxes.append({'object': result["detection_class_entities"][detectedObject].decode("utf-8"),
                                   'score': result["detection_scores"][detectedObject].item(),
                                   'boundBox': result["detection_boxes"][detectedObject].tolist()
                })
        return boundBoxes

    # Perform inference
    print('Exploring image objects with Tensor Flow version ' + str(tf.__version__))
    image_path = download_and_resize_image(imageFile)
    boundBoxes = run_detector(detector, image_path)
    return boundBoxes

'''
# TEST OBJECT DETECTION ON LOCAL IMAGES
print(tfObjectDetection(Image.open('temp/WU-SVK-GMB-C-411.jpg')))
print(tfObjectDetection(Image.open('temp/WU-SVK-GMB-C-4260.jpg')))
print(tfObjectDetection(Image.open('temp/WU-CZE-4RG-O0090.jpg')))
print(tfObjectDetection(Image.open('temp/WU-CZE-4RG-K1320.jpg')))
'''


# CONNECTION TO ELASTIC SEARCH
# Query returning artworks without detected objects
query = {
  "query": {
    "bool": {
      "must": [
        {
          "bool": {
            "must_not": {
              "exists": {
                "field": "detected_objects"
              }
            }
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



# Imports for running inference on the TF-Hub module.
import tensorflow as tf
import tensorflow_hub as hub

# Apply module
module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1" #@param ["https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1", "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"]
detector = hub.load(module_handle).signatures['default']

# Iterating through artworks list

for artwork in artworks:
    imageUrl = 'https://storage.googleapis.com/digital-curator.appspot.com/artworks-all/'+artwork['_id']+'.jpg' # Creating img url from artwork id
    imageFileName = 'temp/'+artwork['_id']+'.jpg' # Creating image file name from artwork id
    print(imageFileName)
    urllib.request.urlretrieve(imageUrl, imageFileName) # Downloading image from url and saving to file name
    image = Image.open(imageFileName)  # Converting to PIL image file
    print(image)
    # Preparing json for upload and calling Tensor Flow object detection
    documentData = {
        "doc": {
            "detected_objects": tfObjectDetection(image),
        },
        "doc_as_upsert": True
    }
    print('Detected objects: ' + str(documentData))
    writeToElastic(artwork['_id'], documentData) # Writing to Digital Curator Elastic Search DB
    print('Data recorded for: ' + imageUrl)
    os.remove(imageFileName) # Removing image


