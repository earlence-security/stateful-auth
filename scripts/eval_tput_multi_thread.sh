#!/bin/sh
log_dir="./tput_$1_threads"
# base_url="http://$2/api"
mkdir -p $log_dir
for i in `seq 1 $1`
do
    python ./eval_tput.py --token BUh0spDAbR8t6wnXGNiHZ7NzlxO2iX4VrN6Iqg4ZqK --base-url http://127.0.0.1:5000 --model stateful --n-objects 1 --delay 0 --time-limit 31 > $log_dir/tput_$i.txt &
done