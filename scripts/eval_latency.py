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
from copy import deepcopy


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
apis_ids = [(e["api"], e["method"]) for e in fake_history_entries if "<event_id>" not in e["api"]]

def generate_requests(n_iters, deny_ratio=0.2, model='stateful'):
    reqs = []
    # Option 1: mix the endpoints
    for i in [1, 10, 20, 30, 40, 50]:
        for _ in range(n_iters):
            path, method = random.choice(apis_ids)
            ids = [str(uuid4()) for _ in range(i)]
            # Fake ids in data.
            data = {'ids': ids}
            # path.replace('<event_id>', id.hex)
            # Replace "<event_id>" with real ids in history.
            if model == 'stateful':
                batch_history = {}
                for id in ids:
                    history = deepcopy(fake_history_entries)
                    for e in history:
                        e["api"] = e["api"].replace('<event_id>', id)
                    batch_history[id] = history
                reqs.append((i, path, method, json.dumps(data), batch_history))
            else:
                reqs.append((i, path, method, json.dumps(data), None))

    # Option 2: measure the latency of every single endpoint
    # ids = []
    # num_requests_each_api = num_requests // len(apis)
    # for i in range(num_requests):
    #     r = random.random()
    #     id = uuid4()
    #     path, method = apis[i // num_requests_each_api]
    #     if '<event_id>' in path:
    #         path = path.replace('<event_id>', str(id))
    #         data = None
    #     else:
    #         data = {'eventId': str(id)}
    #     history = fake_history_entries.copy()
    #     if r < deny_ratio:
    #         history.remove({
    #             "api": "/api/events",          # insert
    #             "method": "POST",
    #             "counter": 0,
    #             "timestamp": 1705279436.833235
    #         })
    #     for e in history:
    #         e["api"] = e["api"].replace('<event_id>', str(id))
    #     reqs.append((id, path, method, json.dumps(data), history))
    #     ids.append(id)
    return reqs


def measure_latency(base_url, token, reqs):
    latency = []
    for i, path, method, data, batch_history in reqs:
        headers = {
            'Authorization': f'Bearer {token}',
            'Authorization-History': json.dumps(batch_history),
            'Content-Type': 'application/json',
        }
        start_time = time.time()
        # print(f'{method} {path} {data} {headers}')
        print(f"Data size: {len(data)}")
        print(f"Header size: {len(headers['Authorization-History'])}")
        r = requests.request(method, f'{base_url}{path}', data=data, headers=headers)
        end_time = time.time()
        # Convert to ms
        latency.append((end_time - start_time) * 1000)
    return latency


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='token')
    parser.add_argument('--base-url', type=str, default='http://127.0.0.1:5000/api')
    # parser.add_argument('--num-requests', type=int, default=300)
    parser.add_argument('--n-iters', type=int, default=30)
    # parser.add_argument('--max-objects', type=int, default=10)
    # parser.add_argument('--step', type=int, default=1)
    parser.add_argument('--deny-ratio', type=float, default='0.2')
    parser.add_argument('--model', type=str, default='stateful')
    args = parser.parse_args()
    
    reqs = generate_requests(args.n_iters, args.deny_ratio, args.model)
    with open('reqs.json', 'w') as f:
        json.dump(reqs, f, indent=4)

    # with open('reqs.json', 'r') as f:
    #     reqs = json.load(f)

    latency = measure_latency(args.base_url, args.token, reqs)

    with open(f'latency_{args.model}.csv', 'w') as f:
        f.write('num_objects, method,path,latency\n')
        for (i, path, method, _, _), l in zip(reqs, latency):
            f.write(f'{i},{method},{path},{l}\n')


if __name__ == '__main__':
    main()
