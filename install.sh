#!/bin/bash

# copy service files to system locations
cp /home/pi/pager.service /lib/systemd/system/pager.service
cp /home/pi/update.service /lib/systemd/system/update.service

# install new services
systemctl enable pager pager-update
systemctl start pager
