#!/bin/bash

UNITS=/home/pi/pagerpi/systemd
SERVICE_DEF=/lib/systemd/system

# copy service files to system locations
cp $UNITS/pager.service        $SERVICE_DEF/pager.service
cp $UNITS/pager-update.service $SERVICE_DEF/pager-update.service
cp $UNITS/pager-update.timer   $SERVICE_DEF/pager-update.timer

# install new services
systemctl enable pager pager-update pager-update.timer
systemctl start pager
