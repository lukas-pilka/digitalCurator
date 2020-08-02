# -*- coding: utf-8 -*-

def tfObjectDetection(imageFile):

    # Imports and function definitions

    # For running inference on the TF-Hub module.
    import tensorflow as tf
    import tensorflow_hub as hub

    # For downloading the image.
    import tempfile
    from PIL import Image
    from PIL import ImageOps

    # For measuring the inference time.
    import time

    # Download and resize image

    def download_and_resize_image(loadedImage, new_width=256, new_height=256, display=False):
        _, filename = tempfile.mkstemp(suffix=".jpg")
        pil_image = loadedImage
        pil_image = ImageOps.fit(pil_image, (new_width, new_height), Image.ANTIALIAS)
        pil_image_rgb = pil_image.convert("RGB")
        pil_image_rgb.save(filename, format="JPEG", quality=90)
        return filename

    # Apply module

    module_handle = "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1" #@param ["https://tfhub.dev/google/openimages_v4/ssd/mobilenet_v2/1", "https://tfhub.dev/google/faster_rcnn/openimages_v4/inception_resnet_v2/1"]

    detector = hub.load(module_handle).signatures['default']

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
    image_path = download_and_resize_image(imageFile, 640, 480)
    boundBoxes = run_detector(detector, image_path)
    return boundBoxes

