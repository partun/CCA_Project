#!/bin/bash

# python
sudo apt add-apt-repository universe
sudo apt update
sudo apt install python3-pip -y
pip3 install docker psutil


# memcached
sudo apt install -y memcached libmemcached-tools
sudo systemctl status memcached



# docker
sudo docker pull anakli/parsec:dedup-native-reduced
sudo docker pull anakli/parsec:splash2x-fft-native-reduced
sudo docker pull anakli/parsec:ferret-native-reduced
sudo docker pull anakli/parsec:blackscholes-native-reduced
sudo docker pull anakli/parsec:canneal-native-reduced
sudo docker pull anakli/parsec:freqmine-native-reduced
