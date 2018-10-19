#!/usr/bin/env python
import zmq
from copy import copy
from selfdrive import messaging
from selfdrive.services import service_list
from cereal import log
from time import sleep
from common.transformations.coordinates import geodetic2ecef
import requests
import os
import subprocess
import threading

context = zmq.Context()
location = messaging.sub_sock(context, service_list['gpsLocation'].port)
health = messaging.sub_sock(context, service_list['health'].port)
thermal = messaging.sub_sock(context, service_list['thermal'].port)

#initialize the values
#gpsLocation
loc_source = "None"
latitude = -1
longitude = -1
altitude = -1
speed = -1

#health
car_voltage = -1
#thermal
eon_soc = -1
thermal_status = "None"

#the password to get into your homeassistant UI
API_PASSWORD = 'REMOVED'
#the url and what you want to call your EON entity. ie, 'https://myhomeassistanturl.com/api/states/eon.chris'
API_URL = 'https://REMOVED/api/states/eon.chris'
#where you want to ping. probably 'https://myhomeassistanturl.com'
PING_URL = 'REMOVED'

def main(gctx=None):

  while True:
    loc_sock = messaging.recv_one_or_none(location)
    health_sock = messaging.recv_one_or_none(health)
    thermal_sock = messaging.recv_one_or_none(thermal)

    if loc_sock is not None:
      loc_source = loc_sock.gpsLocation.source
      latitude = loc_sock.gpsLocation.latitude
      longitude = loc_sock.gpsLocation.longitude
      altitude = loc_sock.gpsLocation.altitude
      speed = loc_sock.gpsLocation.speed

      print loc_source,
      print latitude,
      print longitude,
      print altitude,
      print speed

    if health_sock is not None:
      car_voltage = health_sock.health.voltage

      print car_voltage

    if thermal_sock is not None:
      eon_soc = thermal_sock.thermal.batteryPercent
      thermal_status = thermal_sock.thermal.thermalStatus

      print eon_soc,
      print thermal_status

      send()
      sleep(3)

def send():
  ready = False

  while not ready:
    ping = subprocess.call(["ping", "-W", "4", "-c", "1", PING_URL])
    if ping:
      #didn't get a good ping. sleep and try again
      sleep(1)
    else:
      ready = True

  while ready:
    print "Transmitting to Home Assistant..."

    headers = {
    'x-ha-access': API_PASSWORD
    }
    print latitude
    stats = {'latitude': latitude,
    'longitude': longitude,
    'altitude': altitude,
    'speed': speed,
    'loc_source': loc_source,
    'car_voltage': car_voltage,
    'eon_soc': eon_soc,
    'thermal_status': thermal_status

    }
    data = {'state': 'connected',
    'attributes': stats,
    }
    r = requests.post(API_URL, headers=headers, json=data)
    if r.status_code == requests.codes.ok:
      print "Received by Home Assistant"
    else:
      print "Problem sending. Retry"

if __name__ == '__main__':
  main()
