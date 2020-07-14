#!/bin/bash 
sudo sh config_files/stop_website.sh
sleep 2s
sudo systemctl start supervisord
sudo service nginx start
