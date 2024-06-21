import argparse
import pandas as pd

def get_breakdown_data(filepath, num_objects, warmup_steps=5):
    breakdown_df = pd.read_json(filepath)
    breakdown_agg = {
        "request_total_time": [],
        "token_validation_time": [],
        "history_validation_time": [],
        "policy_execution_time": [],
        "history_update_time": [],
        "resource_api_time": [],
    }
    for n in num_objects:
        d = breakdown_df[breakdown_df['history_length'] == n * 10]
        for k in breakdown_agg.keys():
            if k in d.columns:
                breakdown_agg[k].append(d.iloc[warmup_steps:][k].mean() * 1000)
    return breakdown_agg

def main():
    parser = argparse.ArgumentParser(description="Summarize a server-side log")
    parser.add_argument("--file", '-f', type=str, help="Path to the log file")
    parser.add_argument("--num-objects", type=str, default="1,10,20,30,40,50", help="Number of objects(separated by comma)")
    parser.add_argument("--warmup-steps", type=int, default=5, help="Number of warmup steps")
    args = parser.parse_args()

    num_objects = [int(i) for i in args.num_objects.split(",")]
    breakdown_agg = get_breakdown_data(args.file, num_objects, args.warmup_steps)
    print('---------------------------------Server-side Latency Breakdown---------------------------------')
    print('NumObjs                    ', ''.join([f'{str(i):>10}' for i in num_objects]))
    print('-----------------------------------------------------------------------------------------------')
    print('Request Total Time(ms)     ', ''.join([f'{breakdown_agg["request_total_time"][i]:10.2f}' for i in range(len(num_objects))]))
    print('-----------------------------------------------------------------------------------------------')
    print('Token Validation Time(ms)  ', ''.join([f'{breakdown_agg["token_validation_time"][i]:10.2f}' for i in range(len(num_objects))]))
    print('-----------------------------------------------------------------------------------------------')
    print('History Validation Time(ms)', ''.join([f'{breakdown_agg["history_validation_time"][i]:10.2f}' for i in range(len(num_objects))]))
    print('-----------------------------------------------------------------------------------------------')
    print('Policy Execution Time(ms)  ', ''.join([f'{breakdown_agg["policy_execution_time"][i]:10.2f}' for i in range(len(num_objects))]))
    print('-----------------------------------------------------------------------------------------------')
    print('History Update Time(ms)    ', ''.join([f'{breakdown_agg["history_update_time"][i]:10.2f}' for i in range(len(num_objects))]))
    print('-----------------------------------------------------------------------------------------------')

if __name__ == "__main__":
    main()