"""
Automate measurement of macaroon-based authorization latency.
"""

import time
import requests
import argparse

def measure_latency(base_url, token, iters, accept=True):
    latency = []
    path = "/api/send-money"
    method = "POST"
    if accept: 
        data = {'recipient': 'Leo', 
                'amount': 10,
                'currency': 'USD'}
    else:
        data = {'recipient': 'Leo', 
                'amount': 1000, 
                'currency': 'USD'}
        
    for i in range (iters + 10):
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        start_time = time.time()
        # print(f'{method} {path} {data} {headers}')
        # print(f"Data size: {len(data)}")
        # print(f"Header size: {len(headers['Authorization-History'])}")
        r = requests.request(method, f'{base_url}{path}', data=data, headers=headers)
        end_time = time.time()
        # warm-up
        if i >= 10:
            latency.append((end_time - start_time) * 1000)
    return latency


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='token')
    parser.add_argument('--base-url', type=str, default='http://127.0.0.1:5000')
    parser.add_argument('--n-iters', type=int, default=30)
    parser.add_argument('--accept', type=bool, default=True)
    args = parser.parse_args()

    latency = measure_latency(args.base_url, args.token, args.n_iters, )
    avg_latency = sum(latency) / len(latency)

    print(f"Latency: {avg_latency}")


if __name__ == '__main__':
    main()
