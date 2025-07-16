#!/bin/bash
set -e

# Update package list and install system packages needed for Kivy
if [ $(id -u) -eq 0 ]; then
    apt-get update
    apt-get install -y python3-pip python3-setuptools python3-wheel build-essential libgl1-mesa-dev libgles2-mesa-dev libgstreamer1.0-dev libmtdev-dev
fi

# Upgrade pip
python3 -m pip install --upgrade pip

# Install python dependencies
python3 -m pip install -r requirements.txt
