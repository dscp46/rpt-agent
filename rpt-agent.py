#!/usr/bin/env python3
import argparse
import os
import paho.mqtt.client as mqtt
import signal
import sys

parser = argparse.ArgumentParser()
parser.add_argument( '-b', '--server', nargs=1, default=['test.mosquitto.org'], type=str, help="MQTT broker address")
parser.add_argument( '-p', '--port', nargs=1, default=1883, type=int, help="MQTT broker port")
parser.add_argument( '-u', '--user', nargs=1, type=str, help="MQTT broker username")
parser.add_argument( '-s', '--password', nargs=1, type=str, help="MQTT broker password")
parser.add_argument( '-c', '--call', nargs=1, type=str, help="Remote repeater callsign", required=True)
parser.add_argument( '-v', '--verbose', help="Increases output verbosity", action="store_true")
parser.add_argument( '-n', '--noreboot', help="Disable system reboot", action="store_true")
global args
args = parser.parse_args()

if args.verbose == True: 
    print(args)

def handle_cmd( cmd, cargs):
    print( "Received command: "+ cmd)
    if cmd == "chmod":
        if args.verbose == True:
            print( "Switching to room "+ cargs[0])
        os.system("nohup /etc/spotnik/restart."+cargs[0]+" > /dev/null &")
    elif cmd == "reboot":
        if args.verbose == True:
            print( "Initiating system reboot")
        if args.noreboot == False:
            os.system("nohup $(which shutdown) -r +1 &")
        else:
            print( "Not rebooting as requested by input options")
    elif cmd == "disc":
        if args.verbose == True:
            print( "Switching to disconnected mode")
        os.system("nohup /etc/spotnik/restart.default > /dev/null &")
    elif cmd == "txon":
        if args.verbose == True:
            print( "Starting svxlink")
        os.system("nohup /etc/spotnik/restart > /dev/null &")
    elif cmd == "txoff":
        if args.verbose == True:
            print( "Stopping Svxlink")
        os.system("/etc/spotnik/num.sh stop")
        os.system("pkill -f svxbridge.py")
        os.system("pgrep -x svxlink && pkill -TERM svxlink")
        os.system("pgrep -x timersalon && pkill -f timersalon")

def on_sigint( signum, frame):
    print( "\nExiting...")
    mqtt_client.disconnect()

# Message handling
def on_message( client, obj, mesg):
    pload = mesg.payload.decode('UTF-8')
    if args.verbose == True: 
        print( "Received message: "+ mesg.topic +" "+str(mesg.qos)+" '"+pload+"'")
    try:
        mparser = None
        if sys.version_info.minor >= 9:
            mparser = argparse.ArgumentParser( add_help=False, exit_on_error=False)
        else:
            mparser = argparse.ArgumentParser( add_help=False)

        mparser.add_argument( 'seq', type=int)
        mparser.add_argument( 'command', type=str, choices=['txon', 'txoff', 'chmod', 'provision', 'reboot', 'disc', 'ping'])
        mparser.add_argument( 'args', nargs='*', type=str)
        cmd = mparser.parse_args( pload.split(' '))

        if mesg.qos == 2:
            mqtt_client.publish( "repeaters/" + args.call[0] + "/v1/response", cmd.seq, 2)

        handle_cmd( cmd.command, cmd.args)
    except:
        if args.verbose == True:
            print( "Ignoring invalid command: "+pload)
        pass

def on_connect( client, userdata, flags, rc):
    print( "Connected with result code: " + str(rc))

    if( rc == 5 ):
        print( "Invalid username or password!, check credentials and try to connect again.")
        exit( 255);
    
    # Subscribe to topics after being connected
    topic = "repeaters/"+args.call[0]+"/v1"
    mqtt_client.subscribe( topic, 0)
    mqtt_client.subscribe( topic, 2)

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

mqtt_client.connect( args.server[0], args.port, 10)

# Handle traffic, callback, reconnecting, etc.
mqtt_client.loop_forever()

