#!/bin/bash

UNITS=/home/pi/pagerpi/systemd
SERVICE_DEF=/lib/systemd/system

# copy service files to system locations
cp $UNITS/pager.service        $SERVICE_DEF/pager.service
cp $UNITS/pager-update.service $SERVICE_DEF/pager-update.service
cp $UNITS/pager-update.timer   $SERVICE_DEF/pager-update.timer

read -p "Papertrail server [enter to ignore papertrail setup] " -e PAPERTRAIL_SERVER

if [ "x" <> "x$PAPERTRAIL_SERVER" ]; then
   read -p "Papertrail port " -e PAPERTRAIL_PORT
   if [ "x" <> "x$PAPERTRAIL_PORT" ]; then
      sed -e "s/PAPERTRAIL_SERVER/$PAPERTRAIL_SERVER/g" \
          -e "s/PAPERTRAIL_PORT/$PAPERTRAIL_PORT/g" \
          $UNITS/papertrail.service > $SERVICE_DEF/papertrail.service
   fi
fi

# install new services
systemctl enable pager pager-update pager-update.timer papertrail.service
systemctl start pager
systemctl start papertrail.service
