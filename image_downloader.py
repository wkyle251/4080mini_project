import redis
import json
import requests
import base64


def download_image(redis_client):
    while True:
        _, message = redis_client.blpop("download")
        data = json.loads(message)
        url = data["url"]
        timestamp = data["timestamp"]
        task_id = data["task_id"]
        try:
            response = requests.get(url)
            response.raise_for_status()

            image_data = base64.b64encode(response.content).decode("utf-8")
            redis_client.rpush(
                "image",
                json.dumps({
                    "timestamp": timestamp,
                    "url": url,
                    "image": image_data,
                    "task_id": task_id,
                })
            )
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")


if __name__ == "__main__":
    redis_client = redis.StrictRedis(
        host="localhost", port=8888, decode_responses=True)
    download_image(redis_client)
