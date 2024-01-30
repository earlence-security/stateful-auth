#!/bin/sh
log_dir="./tput_$1_threads"
# base_url="http://$2/api"
# mkdir -p $log_dir
for i in `seq 1 $1`
do
    python3 ./eval_tput.py --token $3 --base-url $4 --model $2  --n-objects $5 --delay 0 --time-limit 31 --n-threads $1 --thread $i --n-iters 10000 &
done
