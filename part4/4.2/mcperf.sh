#!/bin/bash
sudo apt-get update
sudo apt-get install libevent-dev libzmq3-dev git make g++ --yes
sudo apt-get build-dep memcached --yes
git clone https://github.com/eth-easl/memcache-perf-dynamic.git
cd memcache-perf-dynamic
make

exit 0

# client-agent
# ./mcperf -T 16 -A


# client-measure

# 4.2
./mcperf -s  10.156.15.206 --loadonly
./mcperf -s  10.156.15.206 -a 10.156.15.205 \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1800 \
--qps_interval 10 --qps_min 5000 --qps_max 100000

# 4.3
./mcperf -s  10.156.15.206 --loadonly
date && ./mcperf -s  10.156.15.206 -a 10.156.15.205 \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1500 \
--qps_interval 10 --qps_min 5000 --qps_max 100000 \
--qps_seed 42

# 4.4
./mcperf -s  10.156.15.210 --loadonly
date && ./mcperf -s  10.156.15.210 -a 10.156.15.208 \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1500 \
--qps_interval 5 --qps_min 5000 --qps_max 100000 \
--qps_seed 42

date && ./mcperf -s  10.156.15.210 -a 10.156.15.208 \
--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 1800 \
--qps_interval 3 --qps_min 5000 --qps_max 100000 \
--qps_seed 42

