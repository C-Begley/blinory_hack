#!/bin/bash

systemctl status NetworkManager | grep "inactive"
if [ $? -eq 0 ]; then
    echo "Is the NetworkManager on?"
    exit -1
fi


python -u control_panel.py $@ 2>&1 | grep -v "swscaler"
