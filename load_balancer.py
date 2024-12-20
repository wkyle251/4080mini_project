import redis
import subprocess
import time
from multiprocessing import Process

def monitor_queue():
    redis_client = redis.StrictRedis(host="localhost", port=6379, decode_responses=True)
    max_processes = 10  # Maximum number of instances to spawn
    active_processes = []

    try:
        while True:
            # Check the length of the 'image' queue
            queue_length = redis_client.llen("image")
            print(f"Current queue length: {queue_length}")
            
            # If queue length exceeds the threshold, spawn a new process
            if queue_length > 5 and len(active_processes) < max_processes:
                print("Spawning a new instance of predict.py...")
                process = subprocess.Popen(["python", "predict.py"])
                active_processes.append(process)

            # Check if any processes have exited and remove them from the list
            for process in active_processes[:]:
                if process.poll() is not None:  # If the process has terminated
                    print("A predict.py instance has terminated.")
                    active_processes.remove(process)

            # Sleep for a short interval before checking again
            time.sleep(2)

    except KeyboardInterrupt:
        print("Shutting down load balancer...")
        # Terminate all active processes on exit
        for process in active_processes:
            process.terminate()
        print("All processes terminated.")

if __name__ == "__main__":
    monitor_queue()
