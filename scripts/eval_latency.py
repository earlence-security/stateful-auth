"""
Measure the E2E latency w/ fixed history size (i.e. the history will contain all the APIs).
Every policy runs will succeed.
We have a fake history, the server stored a fake history for each new object and perform check and update as usual.
"""
import time
import json
import requests
import argparse
import random
from uuid import uuid4


# Google Calendar events have 11 API endpoints. 10 if excluding the delete API.
api_lst = ['get', 'list', 'insert', 'update', 'patch', 'move', 'import', 'watch', 'stop', 'quickAdd']
fake_history_entries = [
    {
        "api": "/api/events/<event_id>",    # get
        "method": "GET",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/import",    # import
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events",          # insert
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/<event_id>/instances",          # instances
        "method": "GET",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events",          # list
        "method": "GET",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/<event_id>/move",          # move
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/<event_id>",    # patch
        "method": "PATCH",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/quickAdd",    # quickAdd
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/<event_id>",    # update
        "method": "PUT",
        "counter": 0,
        "timestamp": 1705279436.833235
    },
    {
        "api": "/api/events/watch",    # watch
        "method": "POST",
        "counter": 0,
        "timestamp": 1705279436.833235
    }
]
apis = [(e["api"], e["method"])  for e in fake_history_entries]


def generate_requests(num_requests, deny_ratio=0.2):
    reqs = []
    # Option 1: mix the endpoints
    # for _ in range(num_requests):
    #     id = uuid4()
    #     path, method = random.choice(apis)
    #     path.replace('<event_id>', id.hex)
    #     history = fake_history_entries.copy()
    #     for e in history:
    #         e["api"] = e["api"].replace('<event_id>', id.hex)
    #     reqs.append((id, path, method, history))

    # Option 2: measure the latency of every single endpoint
    ids = []
    num_requests_each_api = num_requests // len(apis)
    for i in range(num_requests):
        r = random.random()
        id = uuid4()
        path, method = apis[i // num_requests_each_api]
        if '<event_id>' in path:
            path = path.replace('<event_id>', str(id))
            data = None
        else:
            data = {'eventId': str(id)}
        history = fake_history_entries.copy()
        if r < deny_ratio:
            history.remove({
                "api": "/api/events",          # insert
                "method": "POST",
                "counter": 0,
                "timestamp": 1705279436.833235
            })
        for e in history:
            e["api"] = e["api"].replace('<event_id>', str(id))
        reqs.append((id, path, method, json.dumps(data), history))
        ids.append(id)
    return reqs


def measure_latency(base_url, token, reqs):
    latency = []
    for id, path, method, data, history in reqs:
        headers = {
            'Authorization': f'Bearer {token}',
            'Authorization-History': json.dumps({id.hex: history}),
        }
        start_time = time.time()
        # print(f'{method} {path} {data} {headers}')
        r = requests.request(method, f'{base_url}{path}', data=data, headers=headers)
        end_time = time.time()
        # Convert to ms
        latency.append((end_time - start_time) * 1000)
    return latency


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='token')
    parser.add_argument('--base-url', type=str, default='http://127.0.0.1:5000/api')
    parser.add_argument('--num-requests', type=int, default=300)
    parser.add_argument('--deny-ratio', type=float, default='0.2')
    args = parser.parse_args()
    
    reqs = generate_requests(args.num_requests, args.deny_ratio)
    latency = measure_latency(args.base_url, args.token, reqs)

    with open('latency-baseline.csv', 'w') as f:
        f.write('method,path,latency\n')
        for (_, path, method, _, _), l in zip(reqs, latency):
            f.write(f'{method},{path},{l}\n')


if __name__ == '__main__':
    main()
