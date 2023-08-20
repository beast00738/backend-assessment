from flask import *
import threading
import json
import random
import os
import time

CONFIG_FILE = 'config.json'


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)


data = load_config()
number_of_workers = int(data["number_of_workers"])
average_delay = int(data["average_delay"])
failure_percentage = int(data["failure_percentage"])


# ----------------------------------------------------------------------------------------------------------

def isRequestSuccessfull():
    a = random.uniform(0, 100)
    return False if (a <= failure_percentage) else True


def randomDelay():
    delay_time = random.uniform(average_delay-0.5, average_delay+0.5)
    time.sleep(delay_time)
    return delay_time


stats = {
    "success-request": {"total": 0},
    "failed-request": {"total": 0},
    "total-request": {"total": 0},
    "avg-request-time": {"total": 0},
}

STATS_FILE = 'stats.json'
file_lock = threading.Lock()


def save_stats():
    with file_lock:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f)


save_stats()


def setDefaultStats(i):
    stats['success-request'].setdefault(f'worker{i+1}', 0)
    stats['failed-request'].setdefault(f'worker{i+1}', 0)
    stats['total-request'].setdefault(f'worker{i+1}', 0)
    stats['avg-request-time'].setdefault(f'worker{i+1}', 0)


def handle_request(i, success_response):
    delay_time = randomDelay()
    n, a = stats['total-request'][f'worker{i+1}'], stats['avg-request-time'][f'worker{i+1}']
    stats['avg-request-time'][f'worker{i+1}'] = round(
        (a*n + delay_time)/(n+1), 2)

    n, a = stats['total-request']['total'], stats['avg-request-time']['total']
    stats['avg-request-time']['total'] = round((a*n + delay_time)/(n+1), 2)

    stats['total-request'][f'worker{i+1}'] += 1
    stats['total-request']['total'] += 1

    if (isRequestSuccessfull()):
        stats['success-request'][f'worker{i+1}'] += 1
        stats['success-request']['total'] += 1
        save_stats()
        return jsonify(success_response)
    else:
        stats['failed-request'][f'worker{i+1}'] += 1
        stats['failed-request']['total'] += 1
        save_stats()
        return "<h1>500 Internal Server Error</h1>", 500


def create_app(i):
    app = Flask(__name__)
    setDefaultStats(i)

    @app.route('/api/v1/hello')
    def hello():
        return handle_request(i, {"message": "hello-world"})

    @app.route('/worker/stats')
    def worker_stats():
        return jsonify(stats)

    return app


def app_run(app, port):
    app.run(port=port)


# -----------------------------------------MAIN-------------------------
if __name__ == '__main__':
    i = 0
    threads = []
    while (i < number_of_workers):
        app = create_app(i)
        t = threading.Thread(target=app_run, args=(app, (5000+i)))
        threads.append(t)
        t.start()
        i += 1

    for thread in threads:
        thread.join()
