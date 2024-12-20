import redis
import json
import threading
from datetime import datetime
import uuid

def user_input_thread(redis_client):
    while True:
        url = input("Please input the URL of the image:\n")
        if url.startswith("http://") or url.startswith("https://"):
            task_id = str(uuid.uuid4())
            message = {
                "task_id": task_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": url
            }
            redis_client.rpush("download", json.dumps(message))

def print_results_thread(redis_client):
    while True:
        _, message = redis_client.blpop("prediction")  # Blocking pop
        result = json.loads(message)
        print("\nResults:")
        print(f"URL: {result['url']}")
        for idx, prediction in enumerate(result["predictions"], 1):
            print(f"{idx}. {prediction['label']} ({prediction['score']:.4f})")

if __name__ == "__main__":
    redis_client = redis.StrictRedis(host="localhost", port=8888, decode_responses=True)
    threading.Thread(target=user_input_thread, args=(redis_client,), daemon=True).start()
    threading.Thread(target=print_results_thread, args=(redis_client,), daemon=True).start()

    threading.Event().wait()
