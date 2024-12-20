from flask import Flask, request, jsonify, render_template, redirect, url_for
import redis
import json
import time
import uuid
from datetime import datetime
from threading import Thread
import base64

app = Flask(__name__)
redis_client = redis.StrictRedis(
    host="localhost", port=6379, decode_responses=True)
RESULT_STORAGE = {}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle form submission
        task_id = str(uuid.uuid4())
        if "file" in request.files and request.files["file"]:
            uploaded_file = request.files["file"]
            if uploaded_file.filename == "":
                return "No file selected. Please upload a valid file.", 400

            file_data = uploaded_file.read()
            file_base64 = base64.b64encode(file_data).decode("utf-8")

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            message = json.dumps({
                "timestamp": timestamp,
                "task_id": task_id,
                "image": file_base64,
                "url": "file"
            })

            redis_client.rpush("image", message)

            RESULT_STORAGE[task_id] = {
                "status": "pending",
                "task_id": task_id,
            }

            return redirect(url_for("result", task_id=task_id))

        image_url = request.form.get("image_url")
        if image_url and image_url.startswith(("http://", "https://")):
            message = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "url": image_url,
                "task_id": task_id,
            }
            print(message)
            redis_client.rpush("download", json.dumps(message))
            RESULT_STORAGE[task_id] = {
                "status": "pending",
                "task_id": task_id,
            }
            return redirect(url_for("result", task_id=task_id))
        
        return "Invalid input. Provide a URL or upload a valid file.", 400

    return render_template("index.html")


@app.route("/result/<string:task_id>")
def result(task_id):
    if task_id not in RESULT_STORAGE:
        return "Invalid task ID or task not found.", 404
    result = RESULT_STORAGE[task_id]

    return jsonify(result)


def update_results():
    while True:
        _, message = redis_client.blpop("prediction")
        data = json.loads(message)
        print(data)
        task_id = data.get("task_id")
        predictions = data.get("predictions")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        if task_id in RESULT_STORAGE:
            RESULT_STORAGE[task_id] = {
                "task_id": task_id,
                "status": "completed",
                "upload_time": data.get("timestamp"),
                "complete_time": current_time,
                "predictions": predictions
            }


if __name__ == "__main__":
    thread = Thread(target=update_results, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=80)
