#!/usr/bin/env python
import time
import zmq
from copy import copy
from selfdrive import messaging
from selfdrive.services import service_list
from cereal import log
import requests
import os
import subprocess

context = zmq.Context()
location = messaging.sub_sock(context, service_list['gpsLocation'].port)
health = messaging.sub_sock(context, service_list['health'].port)
thermal = messaging.sub_sock(context, service_list['thermal'].port)

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
bat_temp = -1

#the password to get into your homeassistant UI
API_PASSWORD = 'REMOVED'
#the url and what you want to call your EON entity. ie, 'https://myhomeassistanturl.com/api/states/eon.chris'
API_URL = 'https://REMOVED/api/states/eon.chris'
#where you want to ping. probably 'myhomeassistanturl.com'
PING_URL = 'REMOVED'

last_read = 0
last_send = 0
time_to_read = 1
time_to_send = 5

def main(gctx=None):
  global last_read
  global last_send

  while 1:
    time_now = time.time()
    #read every n seconds
    if time_now - last_read >= time_to_read:
      last_read = read()
      time_now = time.time()
    #send evern seconds
    if time_now - last_send >= time_to_send:
      last_send = send()
      time_now = time.time()
    time.sleep(1)


def read():
  #gpsLocation
  global loc_source
  global latitude
  global longitude
  global altitude
  global speed
  #health
  global car_voltage
  #thermal
  global eon_soc
  global bat_temp
  try:
    location_sock = messaging.recv_one_or_none(location)
    health_sock = messaging.recv_one_or_none(health)
    thermal_sock = messaging.recv_one_or_none(thermal)
    print "HA-after set socks"

    if location_sock is not None:
      loc_source = location_sock.gpsLocation.source
      latitude = location_sock.gpsLocation.latitude
      longitude = location_sock.gpsLocation.longitude
      altitude = location_sock.gpsLocation.altitude
      speed = location_sock.gpsLocation.speed

    if health_sock is not None:
      car_voltage = health_sock.health.voltage

    if thermal_sock is not None:
      eon_soc = thermal_sock.thermal.batteryPercent
      bat_temp = thermal_sock.thermal.bat * .001
      bat_temp = round(bat_temp)
    #print type(loc_source)
    print "HA-end of read"
  except:
    print "HA-Read Failed"
  return time.time()

def send():
  print "HA-send"

  while 1:
    ping = subprocess.call(["ping", "-W", "4", "-c", "1", PING_URL])
    if ping:
      #didn't get a good ping. sleep and try again
      time.sleep(1)
    else:
      break

  print "Transmitting to Home Assistant..."
  time_sent = time.ctime()

  headers = {
  'x-ha-access': API_PASSWORD
  }

  stats = {'latitude': latitude,
  'longitude': longitude,
  'altitude': altitude,
  'speed': speed,
  'loc_source': 'None',
  'car_voltage': car_voltage,
  'eon_soc': eon_soc,
  'bat_temp': bat_temp
  }
  data = {'state': time_sent,
  'attributes': stats,
  }
  try:
    r = requests.post(API_URL, headers=headers, json=data)
    if r.status_code == requests.codes.ok:
      print "Received by Home Assistant"
    else:
      print "Problem sending. Retry"
  except:
    print "Sending totally failed"
  return time.time()

if __name__ == '__main__':
  main()
