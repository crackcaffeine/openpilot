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

def main(gctx=None):
  context = zmq.Context()
  poller = zmq.Poller()
  loc_sock = messaging.sub_sock(context, service_list['gpsLocation'].port, poller)
  health_sock = messaging.sub_sock(context, service_list['health'].port, poller)
  thermal_sock = messaging.sub_sock(context, service_list['thermal'].port, poller)


  #initialize the values
  #gpsLocation
  loc_source = -1
  latitude = -1
  longitude = -1
  altitude = -1
  speed = -1

  #health
  car_voltage = -1
  #thermal
  eon_soc = -1
  thermal_status = -1

  #the password to get into your homeassistant UI
  API_PASSWORD = 'REMOVED'
  #the url and what you want to call your EON entity. ie, 'https://myhomeassistanturl.com/api/states/eon.chris'
  API_URL = 'https://REMOVED/api/states/eon.chris'
  #where you want to ping. probably 'https://myhomeassistanturl.com'
  PING_URL = 'REMOVED'

  while 1:
    ready = False

    while not ready:
      ping = subprocess.call(["ping", "-W", "4", "-c", "1", PING_URL])
      if ping:
        #didn't get a good ping. sleep and try again
        sleep(15)
      else:
        ready = True

    while ready:
      print "Transmitting to Home Assistant..."

      # get location data
      for loc_sock, event in poller.poll(500):
        msg = loc_sock.recv()
        evt = log.Event.from_bytes(msg)

        loc_source = evt.gpsLocation.source
        latitude = evt.gpsLocation.latitude
        longitude = evt.gpsLocation.longitude
        altitude = evt.gpsLocation.altitude
        speed = evt.gpsLocation.speed

      # get health data
      for health_sock, event in poller.poll(500):
        msg = health_sock.recv()
        evt = log.Event.from_bytes(msg)

        car_voltage = evt.health.voltage

      # get thermal data
      for thermal_sock, event in poller.poll(500):
        msg = thermal_sock.recv()
        evt = log.Event.from_bytes(msg)

        eon_soc = evt.thermal.batteryPercent
        thermal_status = evt.thermal.ThermalStatus


      headers = {
      'x-ha-access': API_PASSWORD
      }

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
      sleep(60)
      ready = False

if __name__ == '__main__':
  main()
