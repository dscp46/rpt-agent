#!/usr/bin/env python3
import argparse
import datetime
import paho.mqtt.client as mqtt
import signal

parser = argparse.ArgumentParser()
parser.add_argument( '-b', '--server', nargs=1, default=['test.mosquitto.org'], type=str, help="MQTT broker address")
parser.add_argument( '-p', '--port', nargs=1, default=1883, type=int, help="MQTT broker port")
parser.add_argument( '-u', '--user', nargs=1, type=str, help="MQTT broker username")
parser.add_argument( '-s', '--password', nargs=1, type=str, help="MQTT broker password")
parser.add_argument( '-c', '--call', nargs=1, type=str, help="Remote repeater callsign", required=True)
parser.add_argument( '-v', '--verbose', help="Increases output verbosity", action="store_true")
parser.add_argument( '-r', '--reliable', help="Enables reliable delivery and expects a reply", action="store_true")
parser.add_argument( 'command', nargs='+', type=str, help="The command to send")
args = parser.parse_args()

global seq
tnow = datetime.datetime.now().timestamp()
seq = ''.join(str(tnow).split('.'))

def on_sigint( signum, frame):
    print( "\nExiting...")
    mqtt_client.disconnect()

# Message handling
def on_message( client, obj, mesg):
    pload = mesg.payload.decode('UTF-8')
    if args.verbose == True:
        print( "Received message: "+ mesg.topic +" "+str(mesg.qos)+" '"+pload+"'")
    if mesg.qos == 2 and seq == pload:
        print( "Repeater '"+args.call[0]+"' ACKed our command.")
        mqtt_client.disconnect()

def on_connect( client, userdata, flags, rc):
    print( "Connected with result code: " + str(rc))

    if args.reliable == True:
        # Subscribe to return channel
        topic = "repeaters/" + args.call[0] + "/v1/response"
        mqtt_client.subscribe( topic, 2)

    # Send command
    topic = "repeaters/" + args.call[0] + "/v1"
    payload = seq + ' ' + ' '.join(args.command)
    qos = 0 if args.reliable == False else 2
    mqtt_client.publish( topic, payload.encode('UTF-8'), qos)

    if args.reliable == False:
        mqtt_client.disconnect()

def on_log(client, obj, level, string):
    print(string)

global mqtt_client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
if args.verbose == True:
    mqtt_client.on_log = on_log

# Handle user break
signal.signal(signal.SIGINT, on_sigint)

if args.user != None and args.user[0] != None and args.password != None and args.password[0] != None:
    mqtt_client.username_pw_set( args.user[0], args.password[0])

mqtt_client.connect( args.server[0], args.port)

mqtt_client.loop_forever()
