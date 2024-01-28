"""
Send asynchronous requests to the server to evaluate the throughput.
"""
import time
import json
import argparse
import httpx
import random
import asyncio
from uuid import uuid4
from itertools import accumulate
from copy import deepcopy
from datetime import datetime
import logging


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

# Global variables
num_completed_reqs = 0
num_completed_reqs_window = 0
num_sent_reqs = 0
start_time = 0
current_time = 0
logs = []  # [(time, counter)]

def generate_requests(n_iters, model='stateful', n_objects=1):
    # Option 1: mix the endpoints
    # for i in [1, 10, 20, 30, 40, 50]:
    reqs = []
    for _ in range(n_iters):
        path, method = random.choice(apis_ids)
        ids = [str(uuid4()) for _ in range(n_objects)]
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
            reqs.append((n_objects, path, method, json.dumps(data), batch_history))
        else:
            reqs.append((n_objects, path, method, json.dumps(data), None))
    # with open(f'reqs_{i}.json', 'w') as f:
    #     json.dump(reqs, f)
    return reqs


async def send_request(client, base_url, token, path, method, data, batch_history):
    global num_completed_reqs, num_sent_reqs, num_completed_reqs_window
    global start_time, current_time
    global logs
    # async with httpx.AsyncClient() as client:
        # start_time = time.time()
    url = f'{base_url}{path}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Authorization-History': json.dumps(batch_history),
        'Content-Type': 'application/json',
    }
    if start_time == 0:
        # Start the timer when sending the first request.
        start_time = time.time()
        current_time = start_time
    num_sent_reqs += 1
    response = await client.request(url=url, method=method, data=data, headers=headers)
    num_completed_reqs += 1
    num_completed_reqs_window += 1
    if time.time() - current_time >= 10:
        logs.append(num_completed_reqs_window / (time.time() - current_time))
        current_time = time.time()
        num_completed_reqs_window = 0


async def measure_throughput(base_url, token, reqs, delay_between_requests=0.05, time_limit=300):

    async with httpx.AsyncClient() as client:
        while True:
            for i, path, method, data, batch_history in reqs:
                await send_request(client, base_url, token, path, method, data, batch_history)
                if delay_between_requests > 0:
                    await asyncio.sleep(delay_between_requests / 1000)
                if time.time() - start_time > time_limit:
                    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='token')
    parser.add_argument('--base-url', type=str, default='http://127.0.0.1:5000/api')
    parser.add_argument('--model', type=str, default='stateful')
    # parser.add_argument('--generate-reqs', action='store_true')
    parser.add_argument('--n-iters', type=int, default=30)
    parser.add_argument('--n-objects', type=int, default=1)
    parser.add_argument('--delay', type=float, default=0.05, help="Delay between requests in ms")
    parser.add_argument('--time-limit', type=int, default=300)
    parser.add_argument('--n-threads', type=int, default=1)
    parser.add_argument('--thread', type=int, default=0)

    args = parser.parse_args()
    reqs = generate_requests(args.n_iters, args.model, args.n_objects)
    # with open(f'reqs_{args.model}.json', 'w') as f:
    #     json.dump(reqs, f)
    # return
    # with open(f'reqs_{args.model}.json', 'r') as f:
    #     reqs = json.load(f)
    asyncio.run(measure_throughput(args.base_url, args.token, reqs, delay_between_requests=args.delay, time_limit=args.time_limit))
    suffix = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    cum_tput = num_completed_reqs / (time.time() - start_time)
    with open(f'tput_{args.model}_{args.n_threads}_{args.thread}_{args.delay}_{suffix}.csv', 'w') as f:
        f.write('time/10,tput\n')
        for i, tput in enumerate(logs):
            f.write(f'{i},{tput}\n')
        f.write(f'-1,{cum_tput}\n')

if __name__ == '__main__':
    main()
