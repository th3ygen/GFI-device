""" 
RPI1:-
chain counting
former outside1
chain timestamp for RPI2 speed calc (device interval)
publish timestamp to topic (device/chain/queue, send number/string)

RPI2:-
chain counting
former inside1
subscribe device/chain/queue
chain speed calc, get timestamp from RPI1

RPI3:-
chain counting
former boi
"""

#!/usr/bin/env python3

import os
import psutil
import serial
import json
import time
import schedule
import paho.mqtt.client as mqtt

# Declaring HOST, PORT
MQTT_HOST = 'server.local'
MQTT_PORT = 1883

# Declaring TOPIC
# FORMER_TOPIC = 'push/device/rpi-1/former'
# # NEW_FORMER_TOPIC = 'data/inside1/former'
# CHAIN_TOPIC = 'push/device/rpi-1/chain'
# Q_CHAIN_TOPIC = 'device/chain/queue'
DEV_TOPIC = 'push/device/rpi-3/deviceStatus'

# Initiate MQTIDDIES!
mqttc = mqtt.Client()
mqttc.connect(MQTT_HOST, MQTT_PORT)

# Global var
prev = 0
isReset = False

# Get raspi CPU usage
def cpu_usage():
    return psutil.cpu_percent()

# Get raspi RAM usage
def ram_usage():
    return psutil.virtual_memory()[2]

# Get raspi temperature
def temperature():
    temp = os.popen("vcgencmd measure_temp").readline()
    currTemp = temp.replace("temp=","").rstrip('\n') 
    return currTemp.replace("'C","")

# Get raspi uptime
def uptime():
    seconds = int(time.time()) - int(psutil.boot_time())
    m, s = divmod(seconds, 60)
    h, m = divmod(m,60)
    d, h = divmod(h, 24)

    return [d, h, m, s]

# Get timestamp
def time_stamp():
    return int(time.time() * 1000)

# Retrieve data and pass to func
def parse_data():
    ser = serial.Serial('/dev/ttyACM0', 57600)
    ser.flushInput()
    while True:
        raw_data = ser.readline()      
        remaining = len(raw_data)
        text = raw_data.decode('utf-8').strip('\r\n')
#         datasplit = data.split(',')
#         filtered = [float(i) for i in datasplit]
        payload = text.split('?')
        label = payload[0]
        obj = payload[1]
        
        items = obj.split('&')
        
        if label == 'chain':
            chain(int(items[0].split('=')[1]))
     
        """ 
        chain()
        id, [0,1,2], timestamp

        former()
        id, yaw, pitch, interval 

        """
        
#         if remaining > 0:
#             # id to determine either CHAIN or FORMER data
#             # 0 for CHAIN
#             # 1 for FORMER
#             id = filtered[0]
# 
#             if id == 0: # if Chain
#                 d = filtered[1]            
#                 chain(d)
#             else: # if former
#                 yaw = filtered[1]
#                 pitch = filtered[2]
#                 interval = filtered[3]
#                 former(yaw, pitch, interval)

# Chain data parser
def chain(d): # All devs
    # d for [0,1,2]
    # 0 for default
    # 1 for chain hit
    # 2 for Reset hit

    def calcInterval(now):
        global prev
        interval = 0
        if prev > 0:
            interval = now - prev
        prev = now
        return interval

    if d == 1:
        interval = calcInterval(time_stamp())
    elif d == 2:
        interval = calcInterval(time_stamp())
    else:
        pass

    if d == 1 or d == 2:
        chain = json.dumps({
            'timestamp': timestamp,
            'interval': interval,
            'reset': (d == 2)
        })
        qChain = json.dumps({
            'timestamp': timestamp
        })
        mqttc.publish(CHAIN_TOPIC, chain)
        mqttc.publish(Q_CHAIN_TOPIC, qChain)
        

    return

# Device status data parser
def device_status():    
    device = json.dumps({
        'status':{
            'cpu':{
                'val': cpu_usage()
            },
            'ram': {
                'val': ram_usage()
            },
            'tmp':{
                'val': temperature()
            },
            'timestamp': time_stamp()
        }
    })
    print(device)
    mqttc.publish(DEV_TOPIC, device)
    return

# Scheduling
schedule.every(5).minutes.do(device_status)

def main():
    while 1:
        schedule.run_pending()
        



if __name__ == "__main__":
    main()
