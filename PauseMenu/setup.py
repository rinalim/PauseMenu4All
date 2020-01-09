#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal
import curses, errno, re
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET


#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.02

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

PATH_PAUSEMENU = '/opt/retropie/configs/all/PauseMenu/'
ES_INPUT = '/opt/retropie/configs/all/emulationstation/es_input.cfg'
RETROARCH_CFG = '/opt/retropie/configs/all/retroarch-joypads/'

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []

def load_es_cfg():
    doc = ET.parse(ES_INPUT)
    root = doc.getroot()
    #tag = root.find('inputConfig')
    tags = root.findall('inputConfig')
    num = 1
    print '\n'
    for i in tags:
        print str(num) + ". " + i.attrib['deviceName']
        num = num+1
    dev_select = input('\nSelect your joystick: ')

    return tags[dev_select-1].attrib['deviceName']

def set_layout():

    print ' -(1)-----  -(2)-----  -(3)----- '
    print ' | X Y L |  | Y X L |  | L Y X | '
    print ' | A B R |  | B A R |  | R B A | '
    print ' ---------  ---------  --------- '

    es_conf = input('\nSelect your joystick layout: ')
    
    f = open(PATH_PAUSEMENU + "/control/layout.cfg", 'w')
    f.write(str(es_conf)+'\n')
    f.close()

def load_retroarch_cfg(dev_name):
    print 'Device Name: ', dev_name, '\n'
    
    retroarch_key = {}
    f = open(RETROARCH_CFG + dev_name + '.cfg', 'r')
    while True:
        line = f.readline()
        if not line: 
            break
        #line = line.replace('\"','')
        line = line.replace('\n','')
        line = line.replace('input_','')
        line = line.replace('_btn','')
        line = line.replace('_axis','')
        words = line.split()
        retroarch_key[words[0]] = words[2].replace('"','')
    f.close()
    
    f = open(PATH_PAUSEMENU + "/control/layout.cfg", 'a')
    f.write(str(retroarch_key)+'\n')
    f.close()

def signal_handler(signum, frame):
    close_fds(js_fds)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def get_devices():
    devs = []
    if sys.argv[1] == '/dev/input/jsX':
        for dev in os.listdir('/dev/input'):
            if dev.startswith('js'):
                devs.append('/dev/input/' + dev)
    else:
        devs.append(sys.argv[1])

    return devs

def open_devices():
    devs = get_devices()

    fds = []
    for dev in devs:
        try:
            fds.append(os.open(dev, os.O_RDONLY | os.O_NONBLOCK ))
        except:
            pass

    return devs, fds


def close_fds(fds):
    for fd in fds:
        os.close(fd)

def read_event(fd):
    while True:
        try:
            event = os.read(fd, event_size)
        except OSError, e:
            if e.errno == errno.EWOULDBLOCK:
                return None
            return False
        else:
            return event

def process_event(event):

    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return -1

    if js_type == JS_EVENT_BUTTON and js_value == 1:
        print ">> button index:", js_number
        return js_number

    return -1


dev_name = load_es_cfg()

if len(sys.argv) > 2 and sys.argv[2] == '-control':
    set_layout()
    
load_retroarch_cfg(dev_name)

btn_select = -1
btn_start = -1
btn_a = -1
event = -1
f = open(PATH_PAUSEMENU + "button.cfg", 'w')
js_devs, js_fds = open_devices()

print "\nPush a button for SELECT"
while btn_select == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_select = process_event(event)
    time.sleep(0.1)

print "Push a button for START"
while btn_start == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_start = process_event(event)
    time.sleep(0.1)

print "Push a button for ButtonA"
while btn_a == -1:
    for fd in js_fds:
        event = read_event(fd)
        if event:
            btn_a = process_event(event)
    time.sleep(0.1)

#f.write(str(axis_up) + "\n" + str(axis_down) + "\n" + str(btn_select) + "\n" + str(btn_start))
f.write(str(btn_select) + " " + str(btn_start) + " " + str(btn_a))
f.close()

os.system("sudo sed -i 's/input_exit_emulator_btn/#input_exit_emulator_btn/g' " 
          + "'/opt/retropie/configs/all/retroarch/autoconfig/"
          + dev_name
          + ".cfg'")
