import redis
import json
import torch
from torchvision import models, transforms
from PIL import Image
import base64
from io import BytesIO
import urllib.request
import os

IMAGENET_CLASSES_URL = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
CLASS_LABELS_FILE = "imagenet_classes.json"


def download_class_labels():
    if not os.path.exists(CLASS_LABELS_FILE):
        print("Downloading ImageNet class labels...")
        urllib.request.urlretrieve(IMAGENET_CLASSES_URL, CLASS_LABELS_FILE)
        print("Downloaded ImageNet class labels.")
    with open(CLASS_LABELS_FILE, "r") as f:
        return json.load(f)


def preprocess_image(image_data):
    preprocess = transforms.Compose([
        transforms.Resize((299, 299)),  # For InceptionV3 input size
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[
                             0.229, 0.224, 0.225]),
    ])
    image = Image.open(BytesIO(base64.b64decode(image_data))).convert("RGB")
    return preprocess(image).unsqueeze(0)


def predict_labels(model, input_tensor, class_labels):
    model.eval()
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        top5 = torch.topk(probabilities, 5)
        indices = top5.indices.tolist()
        scores = top5.values.tolist()
        return [
            {"label": class_labels[indices[i]], "score": scores[i]} for i in range(5)
        ]


def prediction_service(redis_client, model, class_labels):
    while True:
        # Blocking pop from Redis queue
        _, message = redis_client.blpop("image")
        data = json.loads(message)
        url = data["url"]
        timestamp = data["timestamp"]
        image_data = data["image"]
        task_id = data["task_id"]

        try:
            # Preprocess image and predict labels
            input_tensor = preprocess_image(image_data)
            predictions = predict_labels(model, input_tensor, class_labels)

            # Push the predictions to the "prediction" queue
            redis_client.rpush(
                "prediction",
                json.dumps({"predictions": predictions,
                            "url": url,
                            "timestamp": timestamp,
                            "task_id": task_id,
                            })
            )
        except Exception as e:
            print(f"Error processing image from {url}: {e}")


if __name__ == "__main__":
    redis_client = redis.StrictRedis(
        host="localhost", port=8888, decode_responses=True)

    model = models.inception_v3(weights=models.Inception_V3_Weights.DEFAULT)

    class_labels = download_class_labels()

    prediction_service(redis_client, model, class_labels)
