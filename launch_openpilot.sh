#!/usr/bin/bash

#export PASSIVE="0"
export PASSIVE=$(( $(cat /sys/class/switch/tri-state-key/state) != 3 ? 0 : 1 ))
exec ./launch_chffrplus.sh
