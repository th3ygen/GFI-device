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
import telepot

# Declaring HOST, PORT
MQTT_HOST = 'server.local'
MQTT_PORT = 1883

# Declaring TOPIC
FORMER_TOPIC = 'push/device/rpi-1/former'
# NEW_FORMER_TOPIC = 'data/inside1/former'
CHAIN_TOPIC = 'push/device/rpi-1/chain'
Q_CHAIN_TOPIC = 'device/chain/queue'
DEV_TOPIC = 'push/device/rpi-1/deviceStatus'
SPEED_TOPIC = 'current/data/speed'
SPEED_CALC_TOPIC = 'calc/data/speed'

RAW_FORMER_TOPIC = 'raw/device/rpi-1/former'
RAW_CHAIN_TOPIC = 'raw/device/rpi-1/chain'

DEFAULT_SPEED = 480
RESET_INDEX = 3823

# Initiate MQTIDDIES!
mqttc = mqtt.Client()
mqttc.connect(MQTT_HOST, MQTT_PORT)

# Global var
prev = 0
isReset = False
currentSpeed = DEFAULT_SPEED
reset_count = 1
count = 1
countF = 0
formerReset = False
formerRawReset = False

chat_id = '-478461174'
TOKEN = '1212958603:AAEX78idL5XEK2NsL9uxlNep4jjfs2rCx-4'

bye = [
    "Aite fellas, see ya on the next cycle.",
    "That\'s all for now.",
    "See ya later mate.",
    "I\'ll be back (read with Terminator voice)",
    "Adios"
    ]

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
        schedule.run_pending() 
        raw_data = ser.readline()      
        text = raw_data.decode('utf-8').strip('\r\n')
        payload = text.split('?')
        label = payload[0]
        obj = payload[1]
        
        items = obj.split('&')    
        
            
        if label == 'chain':
            dist = float(items[0].split('=')[1])
            d = int(items[1].split('=')[1])
            global count
            count += 1
            print(count, label,"dist=", dist)
#             if count == 3823:
#                 count = 0
            chain(d)
            
        elif label == 'former':
            print(count, label)          
            former(float(items[0].split('=')[1]), float(items[1].split('=')[1]), count)
            
        elif label == 'formerRaw':
            print(count, label)            
            formerRaw(float(items[0].split('=')[1]), float(items[1].split('=')[1]), float(items[2].split('=')[1]),float(items[3].split('=')[1]), count)            
        else:
            pass
                
        """ 
        chain()
        id, [0,1,2], timestamp

        former()
        id, yaw, pitch, interval 

        """    

# Chain data parser
def chain(d): # All devs
    # d for [0,1,2]
    # 0 for default
    # 1 for chain hit
    # 2 for Reset hit
    global count
    def calcInterval(now):
        global prev
        interval = 0
        if prev > 0:
            interval = now - prev
        prev = now
        return interval

    if d == 1 or d == 2:
        now = time_stamp()
        interval = calcInterval(now)
        
        global reset_count
        reset_count += 1
        
        reset = (d == 2)
        formerReset = reset
        formerRawReset = reset
        
        speed = 200 / (interval / 1000)
        
        if reset:
            #report(dist, count)
            print(reset)
            reset_count = 1
            count = 1
    
        chain = json.dumps({
            'timestamp': now,
            'interval': interval,
            'reset': reset,
            'speed': speed,
            'index': count
        })
        
        chain_raw = json.dumps({
            'timestamp': now,
            'interval': interval,
            'reset': reset,
            'speed': speed,
            'index': count
        })        
        
        qChain = json.dumps({
            'timestamp': now,
            'currentSpeed': speed
        })
        print(speed)
        mqttc.publish(Q_CHAIN_TOPIC, qChain)
        mqttc.publish(CHAIN_TOPIC, chain)
        mqttc.publish(RAW_CHAIN_TOPIC, chain_raw)                    
        
    return

def report(dist, count):
    status = [
        "Anchor Reset Report",
         f"Peak Value at {dist}",
         f"Reset at Index {count}"
         "",
         random.choice(bye)
         ]
    status = '\n'.join(status)
    status = ''.join(map(str, status))
    print(status) 
    send(status)

def send(status):
    bot = telepot.Bot(TOKEN)
    bot.sendMessage(chat_id, status) 

def on_connect(client, userdata, flag, rc):
    client.subscribe(SPEED_TOPIC)

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    if msg.topic == SPEED_TOPIC:
        speed(payload['speed'])

# get current speed
def speed(speed):
    global currentSpeed
    currentSpeed = speed

def former(yawInterval, pitch, index):
    global formerReset
    # Parse data into JSON 
    former = json.dumps({
        'delta': {
            'yaw': yawInterval,
            'pitch': pitch
        },
        
        'timestamp':time_stamp(),
        'index': index,
        'reset': formerReset
    })
    
    formerReset = False

    mqttc.publish(FORMER_TOPIC, former)
    return

# Former data parser
def formerRaw(top_peak, mid_peak, delta_left, delta_right, index):
    global formerRawReset
    # Parse data into JSON 
    former_raw = json.dumps({
        'yaw': {
            'left': delta_left,
            'right': delta_right
        },
        'pitch': {
            'top': top_peak,
            'mid': mid_peak
        },
        
        'timestamp':time_stamp(),
        'index': index,
        'reset': formerRawReset
    })
    
    formerRawReset = False

    mqttc.publish(RAW_FORMER_TOPIC, former_raw)    
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

    mqttc.publish(DEV_TOPIC, device)
    return

# Scheduling
schedule.every(5).minutes.do(device_status)

def main():
    try:
        parse_data()
    finally:        
        main()


if __name__ == "__main__":
    main()
