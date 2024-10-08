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
from datetime import datetime

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
        r = requests.request(method, f'{base_url}{path}', data=data, headers=headers)
        end_time = time.time()
        # Convert to ms
        latency.append((end_time - start_time) * 1000)
    return latency

def eval_latency(latency_map, warmup_steps=5):
    print('------------------Average Latency------------------')
    print('   NumObjs          Average End-to-End Latency(ms) ')
    print('---------------------------------------------------')
    for i, latencies in latency_map.items():
        if len(latencies) <= warmup_steps:
            raise ValueError('Not enough samples')
        print(f'{i:10} {sum(latencies[warmup_steps:])/len(latencies[warmup_steps:]):30.2f}')
        print('---------------------------------------------------')

def main():
    t = time.time()
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='token')
    parser.add_argument('--base-url', type=str, default='http://127.0.0.1:5000')
    parser.add_argument('--n-iters', type=int, default=30)
    parser.add_argument('--deny-ratio', type=float, default='0.2')
    parser.add_argument('--mode', type=str, default='stateful')
    args = parser.parse_args()
    
    reqs = generate_requests(args.n_iters, args.deny_ratio, args.mode)
    # with open('reqs.json', 'w') as f:
    # json.dump(reqs, f, indent=4)

    # with open('reqs.json', 'r') as f:
    #     reqs = json.load(f)

    latency = measure_latency(args.base_url, args.token, reqs)
    latency_map = {}
    suffix = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    with open(f'latency_{args.mode}_{suffix}.csv', 'w') as f:
        f.write('num_objects, method,path,latency\n')
        for (i, path, method, _, _), l in zip(reqs, latency):
            # Write to csv
            f.write(f'{i},{method},{path},{l}\n')
            # Add to latency map
            if i not in latency_map:
                latency_map[i] = []
            latency_map[i].append(l)
    eval_latency(latency_map)
    print("Runtime:", f"{(time.time() - t) * 1000:.2f} ms")

if __name__ == '__main__':
    main()
