import struct

import common.numpy_fast as np
from selfdrive.config import Conversions as CV
from common.fingerprints import HYUNDAI as CAR

# *** Hyundai specific ***
def can_cksum(mm):
  s = 0
  for c in mm:
    c = ord(c)
    s += (c>>4)
    s += c & 0xF
  s = 8-s
  s %= 0x10
  return s


def fix(msg, addr):
  msg2 = msg[0:-1] + chr(ord(msg[-1]) | can_cksum(struct.pack("I", addr)+msg))
  return msg2


def make_can_msg(addr, dat, idx, alt):
  if idx is not None:
    dat += chr(idx << 4)
    dat = fix(dat, addr)
  return [addr, 0, dat, alt]


# def create_brake_command(packer, apply_brake, pcm_override, pcm_cancel_cmd, chime, fcw, idx):
#   """Creates a CAN message for the Honda DBC BRAKE_COMMAND."""
#   pump_on = apply_brake > 0
#   brakelights = apply_brake > 0
#   brake_rq = apply_brake > 0
#   pcm_fault_cmd = False
#
#   values = {
#     "COMPUTER_BRAKE": apply_brake,
#     "COMPUTER_BRAKE_REQUEST": pump_on,
#     "CRUISE_OVERRIDE": pcm_override,
#     "CRUISE_FAULT_CMD": pcm_fault_cmd,
#     "CRUISE_CANCEL_CMD": pcm_cancel_cmd,
#     "COMPUTER_BRAKE_REQUEST_2": brake_rq,
#     "SET_ME_0X80": 0x80,
#     "BRAKE_LIGHTS": brakelights,
#     "CHIME": chime,
#     "FCW": fcw << 1,  # TODO: Why are there two bits for fcw? According to dbc file the first bit should also work
#   }
#   return packer.make_can_msg("BRAKE_COMMAND", 0, values, idx)


# def create_gas_command(packer, gas_amount, idx):
#   """Creates a CAN message for the Honda DBC GAS_COMMAND."""
#   enable = gas_amount > 0.001
#
#   values = {"ENABLE": enable}
#
#   if enable:
#     values["GAS_COMMAND"] = gas_amount * 255.
#     values["GAS_COMMAND2"] = gas_amount * 255.
#
#   return packer.make_can_msg("GAS_COMMAND", 0, values, idx)


def create_steering_control(packer, apply_steer, car_fingerprint, idx):
  """Creates a CAN message for the Hyundai  STEERING and UI."""
  lkas_hud_values = {
    #checksum and counter are calculated elsewhere
    'CF_Lkas_LdwsSysState' : hud.lanes,
    'CF_Lkas_SysWarning' : hud.steer_required,
    'CF_Lkas_LdwsLHWarning' : 0x0,
    'CF_Lkas_LdwsRHWarning' : 0x0,
    'CF_Lkas_HbaLamp' : 0x0,
    'CF_Lkas_FcwBasReq' : 0x0,
    'CR_Lkas_StrToqReq' : apply_steer, #actual torque request
    'CF_Lkas_ActToi': apply_steer != 0, #the torque request bit
    'CF_Lkas_ToiFlt' : 0x0,
    'CF_Lkas_HbaSysState' : 0x1,
    'CF_Lkas_FcwOpt' : 0x0,
    'CF_Lkas_HbaOpt' : 0x1,
    'CF_Lkas_FcwSysState' : 0x0,
    'CF_Lkas_FcwCollisionWarning' : 0x0,
    'CF_Lkas_FusionState' : 0x0,
    'CF_Lkas_FcwOpt_USM' : 0x0,
    'CF_Lkas_LdwsOpt_USM' : 0x3,
  }

  return packer.make_can_msg("LKAS11", 0, lkas_hud_values, idx)


# def create_radar_commands(v_ego, car_fingerprint, idx):
#   """Creates an iterable of CAN messages for the radar system."""
#   commands = []
#   v_ego_kph = np.clip(int(round(v_ego * CV.MS_TO_KPH)), 0, 255)
#   speed = struct.pack('!B', v_ego_kph)
#
#   msg_0x300 = ("\xf9" + speed + "\x8a\xd0" +
#                ("\x20" if idx == 0 or idx == 3 else "\x00") +
#                "\x00\x00")
#
#   if car_fingerprint == CAR.CIVIC:
#     msg_0x301 = "\x02\x38\x44\x32\x4f\x00\x00"
#     commands.append(make_can_msg(0x300, msg_0x300, idx + 8, 1))  # add 8 on idx.
#   else:
#     if car_fingerprint == CAR.CRV:
#       msg_0x301 = "\x00\x00\x50\x02\x51\x00\x00"
#     elif car_fingerprint == CAR.ACURA_RDX:
#       msg_0x301 = "\x0f\x57\x4f\x02\x5a\x00\x00"
#     elif car_fingerprint == CAR.ODYSSEY:
#       msg_0x301 = "\x00\x00\x56\x02\x55\x00\x00"
#     elif car_fingerprint == CAR.ACURA_ILX:
#       msg_0x301 = "\x0f\x18\x51\x02\x5a\x00\x00"
#     elif car_fingerprint == CAR.PILOT:
#       msg_0x301 = "\x00\x00\x56\x02\x58\x00\x00"
#     elif car_fingerprint == CAR.RIDGELINE:
#       msg_0x301 = "\x00\x00\x56\x02\x57\x00\x00"
#     commands.append(make_can_msg(0x300, msg_0x300, idx, 1))
#
#   commands.append(make_can_msg(0x301, msg_0x301, idx, 1))
#   return commands
