#-*-coding: utf-8 -*-
#!/usr/bin/python

import os, sys, struct, time, fcntl, termios, signal
import curses, errno
from pyudev import Context
from subprocess import *
import xml.etree.ElementTree as ET
#from PIL import Image, ImageDraw, ImageFont
import ast

#    struct js_event {
#        __u32 time;     /* event timestamp in milliseconds */
#        __s16 value;    /* value */
#        __u8 type;      /* event type */
#        __u8 number;    /* axis/button number */
#    };

reload(sys)
sys.setdefaultencoding('utf-8')

JS_MIN = -32768
JS_MAX = 32768
JS_REP = 0.20

JS_THRESH = 0.75

JS_EVENT_BUTTON = 0x01
JS_EVENT_AXIS = 0x02
JS_EVENT_INIT = 0x80

CONFIG_DIR = '/opt/retropie/configs/'
RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_PAUSEMENU = CONFIG_DIR + 'all/PauseMenu4All/'	
VIEWER = "pqiv -c -i -c --display=:0 "
#VIEWER_BG = PATH_PAUSEMENU + "omxiv-pause " + PATH_PAUSEMENU + "pause_bg.png -l 29999 -a fill"
#VIEWER_OSD = PATH_PAUSEMENU + "omxiv-pause /tmp/pause.txt -f -t 5 -T blend --duration 200 -l 30001 -a center --win 980,864,1280,1024"

SELECT_BTN_ON = False
START_BTN_ON = False
UP_ON = False
DOWN_ON = False
PAUSE_MODE_ON = False
MENU_INDEX = 0

event_format = 'IhBB'
event_size = struct.calcsize(event_format)
js_fds = []
btn_select = -1
btn_start = -1
btn_a = -1

PATH_PAUSEOPTION = PATH_PAUSEMENU+'control/'
XML = PATH_PAUSEOPTION+'xml/'
FONT = "NanumBarunGothic-Bold"

retroarch_key = {}
user_key = {}
btn_map = {}
kor_map = {
    "Jab": "약",
    "Strong": "중",
    "Fierce": "강",
    "Short": "약",
    "Roundhouse": "강",
    "Light": "약",
    "Middle": "중",
    "Heavy": "강",
    "Punch": "펀치",
    "Kick": "킥", 
    "Attack": "공격",
    "Jump": "점프",
    "Select": "선택",
    "Magic": "마법",
    "Fire": "총알",
    "Loop": "회전",
    "Bubble": "방울",
    "Left": "왼쪽",
    "Center": "가운데",
    "Right": "오른쪽",
    " - ": "-"
}
sys_map = {
    "lr-fbneo": "FinalBurn Neo",
    "lr-fbalpha": "FB Alpha"
}
es_conf = 1
romname = ""

capcom_fight = [
    'mshvsf', 'vsav', 
    'sfa', 'sfa2', 'sfa3', 
    'sf2', 'sf2ce', 'ssf2',
    'sfiii', 'sfiii3'
    ]
capcom_dd = ['ddtod', 'ddsom']


def run_cmd(cmd):
    # runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def check_update():
    RESUME = PATH_PAUSEOPTION + romname + '_resume.png'
    #CORECFG = CONFIG_DIR + 'fba/FB Alpha/FB Alpha.rmp'
    #GAMECFG = CONFIG_DIR + 'fba/FB Alpha/' + romname + '.rmp'
    CORECFG = CONFIG_DIR + 'fba/FinalBurn Neo/FinalBurn Neo.rmp'
    GAMECFG = CONFIG_DIR + 'fba/FinalBurn Neo/' + romname + '.rmp'
   
    if os.path.isfile(RESUME) == False:
        return True
    else:
        _time = os.path.getmtime(RESUME)
        if _time < os.path.getmtime(PATH_PAUSEOPTION+'layout.cfg'):
            return True
        elif os.path.isfile(XML+romname+'.xml') == True:
            if _time < os.path.getmtime(XML+romname+'.xml'):
                return True
        elif os.path.isfile(CORECFG) == True:
            if _time < os.path.getmtime(CORECFG):
                return True
        elif os.path.isfile(GAMECFG) == True:
            if _time < os.path.getmtime(GAMECFG):
                return True
        
    # print 'No need to update PNG'
    return False

def control_on():
    if len(sys.argv) > 2 and sys.argv[2] == '-control':
        return True
    else:
        return False

def load_layout():

    global es_conf, retroarch_key

    #' -(1)-----  -(2)-----  -(3)----- '
    #' | X Y L |  | Y X L |  | L Y X | '
    #' | A B R |  | B A R |  | R B A | '
    #' ---------  ---------  --------- '

    f = open(PATH_PAUSEOPTION+"layout.cfg", 'r')
    es_conf = int(f.readline())

    if es_conf == 1:
        user_key['1'] = 'x'
        user_key['2'] = 'y'
        user_key['3'] = 'l'
        user_key['4'] = 'a'
        user_key['5'] = 'b'
        user_key['6'] = 'r'
    elif es_conf == 2:
        user_key['1'] = 'y'
        user_key['2'] = 'x'
        user_key['3'] = 'l'
        user_key['4'] = 'b'
        user_key['5'] = 'a'
        user_key['6'] = 'r'
    elif es_conf == 3:
        user_key['1'] = 'l'
        user_key['2'] = 'y'
        user_key['3'] = 'x'
        user_key['4'] = 'r'
        user_key['5'] = 'b'
        user_key['6'] = 'a'

    if control_on() == True:
        retroarch_key = ast.literal_eval(f.readline())
    f.close()

def get_info():

    #INPUT = './controls.xml'   
    if os.path.isfile(XML+romname+'.xml') == False:
        print 'No xml found'
        name = romname
        buttons = ['A 버튼', 'B 버튼', 'C 버튼', 'D 버튼', 'None', 'None']
    else:
        doc = ET.parse(XML+romname+'.xml')
        game = doc.getroot()
    #game = root.find('./game[@romname=\"' + romname + '\"]')
    #if game == None:
    #   print 'No Game Found'
        name = str(unicode(game.get('gamename')))
        print 'Generate pause images for ' + name
        player = game.find('player')
        controls = player.find('controls')
        labels = player.findall('labels')
        buttons = []
        for i in labels[0]:
            if 'BUTTON' in i.get('name'):
                btn = str(unicode(i.get('value')))
                # Translate to Korean
		for key in kor_map:
                    if key in btn:
                        btn = btn.replace(key, kor_map[key])
		#btn = btn[:10]
                buttons.append(btn)
                print i.get('name'), btn
        for j in range(len(buttons), 6):
            buttons.append("None")
    
    return buttons


def get_btn_layout(system, buttons):

    # FBA button sequence   
    btn_map['b'] = '"0"'
    btn_map['a'] = '"8"'
    btn_map['y'] = '"1"'
    btn_map['x'] = '"9"'
    btn_map['l'] = '"10"'
    btn_map['r'] = '"11"'

    #if os.path.isfile(CONFIG_DIR + 'fba/FinalBurn Neo/' + romname + '.rmp') == True:
    if os.path.isfile(CONFIG_DIR + 'fba/' + sys_map[system] + '/' + romname + '.rmp') == True:
        print 'Use game specific setting'
        #f = open(CONFIG_DIR + 'fba/FinalBurn Neo/' + romname + '.rmp', 'r')
        f = open(CONFIG_DIR + 'fba/' + sys_map[system] + '/' + romname + '.rmp', 'r')
        while True:
            line = f.readline()
            if not line: 
                break
            if 'btn' not in line:
                continue
            line = line.replace('\n','')
            line = line.replace('input_','')
            line = line.replace('_btn','')
            line = line.replace('=','')
            words = line.split()
            if 'player1' in words[0]:    # input_player1_btn_a = "1"
                btn_map[words[0][8]] = words[1]  
        f.close()
	
    #elif os.path.isfile(CONFIG_DIR + 'fba/FinalBurn Neo/FinalBurn Neo.rmp') == True:
    elif os.path.isfile(CONFIG_DIR + 'fba/' + sys_map[system] + '/' + sys_map[system] + '.rmp') == True:
        print 'Use FinalBurn setting'
        #f = open(CONFIG_DIR + 'fba/FinalBurn Neo/FinalBurn Neo.rmp', 'r')
        f = open(CONFIG_DIR + 'fba/' + sys_map[system] + '/' + sys_map[system] + '.rmp', 'r')
	while True:
            line = f.readline()
            if not line: 
                break
            if 'btn' not in line:
                continue
            line = line.replace('\n','')
            line = line.replace('input_','')
            line = line.replace('_btn','')
            line = line.replace('=','')
            words = line.split()
            if 'player1' in words[0]:    # input_player1_btn_a = "1"
                btn_map[words[0][8]] = words[1]  
        f.close()

    #print btn_map

    # Convert from the FBA sequence to the normal sequence (0~5)
    convert = {}

    if romname in capcom_fight:
        convert['"0"'] = 3
        convert['"8"'] = 4
        convert['"1"'] = 0
        convert['"9"'] = 1
        convert['"10"'] = 2
        convert['"11"'] = 5
    elif romname in capcom_dd:
        convert['"0"'] = 0
        convert['"8"'] = 1
        convert['"1"'] = 3
        convert['"9"'] = 2
        convert['"10"'] = 4
        convert['"11"'] = 5
    else:
        convert['"0"'] = 0
        convert['"8"'] = 1
        convert['"1"'] = 2
        convert['"9"'] = 3
        convert['"10"'] = 4
        convert['"11"'] = 5 

    # Map the button sequnece and the button description   
    btn_map['a'] = buttons[convert[btn_map['a']]]
    btn_map['b'] = buttons[convert[btn_map['b']]]
    btn_map['x'] = buttons[convert[btn_map['x']]]
    btn_map['y'] = buttons[convert[btn_map['y']]]
    btn_map['l'] = buttons[convert[btn_map['l']]]
    btn_map['r'] = buttons[convert[btn_map['r']]]
    #print btn_map

def get_location():
    if is_running("bin/retroarch") == True:
        game_conf = run_cmd("ps -ef | grep emulators | grep -v grep | awk '{print $13}'").rstrip()+".cfg"
        if os.path.isfile(game_conf) == True:
            res = run_cmd("cat " + game_conf + " | grep video_rotation").replace("\n","")
            if len(res) > 1:
                if res.split(' ')[2] == '"1"':
                    return " -o 270"
                elif res.split(' ')[2] == '"3"':
                    return " -o 90"
            #else:
            #    print "No game conf"
        sys_conf = run_cmd("ps -ef | grep emulators | grep -v grep | awk '{print $12}'").rstrip()
        res = run_cmd("cat " + sys_conf + " | grep video_rotation").replace("\n","")
        if len(res) > 1:
            if res.split(' ')[2] == '"1"':
                return " -o 270"
            elif res.split(' ')[2] == '"3"':
                return " -o 90"
    return ""

def get_turbo_key():
    rom_config = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $13}'").replace("\n","")+".cfg"
    if os.path.isfile(rom_config) == True:
        line = run_cmd("cat " + rom_config + " | grep input_player1_turbo_btn")
        if len(line.split()) == 3:
            return line.split()[2]
    return '-1'

def draw_text(text, outfile):
    font_size = 54
    font = ImageFont.truetype('NanumBarunGothicBold.ttf', font_size)
    '''
    while font.getsize(unicode(text))[0] <= 50:
        fontsize -= 1
        font = ImageFont.truetype('NanumBarunGothicBold.ttf', font_size)
        print font.getsize(unicode(text))[0]
    '''
    image = Image.new('RGBA', (font.getsize(unicode(text))[0], font.getsize(unicode(text))[1]), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    '''
    draw.text((0,0), unicode(text), font=font, fill="white")
    draw.text((1,0), unicode(text), font=font, fill="white")
    draw.text((0,1), unicode(text), font=font, fill="white")
    draw.text((1,1), unicode(text), font=font, fill="white")
    '''
    draw.text((0,0), unicode(text), font=font, fill="black")
    image.save(outfile)

def draw_picture(system, buttons):

    CONTROL = " " + PATH_PAUSEOPTION + romname + '_control.png'
    RESUME = " " + PATH_PAUSEOPTION + romname + '_resume.png'
    STOP = " " + PATH_PAUSEOPTION + romname + '_stop.png'

    # Layout
    #cmd = "composite -geometry 300x160+8+185 " + PATH_PAUSEOPTION + "images/layout" + str(es_conf) + ".png" + " images/bg_resume.png" + RESUME
    cmd = "cp " + PATH_PAUSEOPTION + "images/layout" + str(es_conf) + ".png" + CONTROL
    os.system(cmd)

    if system == "lr-fbneo" or system == "lr-fbalpha":
        get_btn_layout(system, buttons)
        # Configured button layout
        #pos = ["90x25+70+253", "90x25+150+227", "90x25+230+204", "90x25+70+318", "90x25+150+293", "90x25+230+267"]
        pos = ["80x22+62+67", "80x22+142+41", "80x22+222+17", "80x22+62+132", "80x22+142+108", "80x22+222+82"]
        for i in range(1,7):
            btn = btn_map[user_key[str(i)]]
            if btn != 'None':
                # check turbo key
                if retroarch_key[user_key[str(i)]] == get_turbo_key():
                    btn = btn+"*"
                #cmd = "convert -background none -fill black -font " + FONT + " -pointsize 20 label:\'" + btn + "\' /tmp/text.png"
                #run_cmd(cmd)
                draw_text(btn, "/tmp/text.png")
                cmd = "composite -geometry " + pos[i-1] + " /tmp/text.png" + CONTROL + CONTROL
                os.system(cmd)

    # Generate a PAUSE image
    cmd = "composite -geometry 300x160+8+185 " + CONTROL + " " + PATH_PAUSEOPTION + "images/bg_resume.png" + RESUME
    os.system(cmd)
    # Generate a STOP image
    cmd = "composite " + PATH_PAUSEOPTION + "images/bg_stop.png " + RESUME + STOP
    os.system(cmd)
    # Generate a Controll image
    cmd = "composite " + CONTROL + " " + PATH_PAUSEOPTION + "images/bg_control.png" + CONTROL
    os.system(cmd)

def start_viewer():
    if control_on() == True and os.path.isfile(PATH_PAUSEOPTION + romname + "_resume.png") == True :
        os.system(VIEWER + PATH_PAUSEOPTION + romname + "_resume.png")
    else:
        os.system(VIEWER + PATH_PAUSEOPTION + "pause_resume.png")

    #os.system(VIEWER_BG + " &")
    #os.system(VIEWER + get_location() + " &")
	
def stop_viewer():
    if is_running("pqiv") == True:
        os.system("killall pqiv")
    
def change_viewer(position):
    if is_running("pqiv") == True:
        os.system("killall pqiv")
    if position == "UP":
        if control_on() == True and os.path.isfile(PATH_PAUSEOPTION + romname + "_resume.png") == True :
            os.system(VIEWER + PATH_PAUSEOPTION + romname + "_resume.png")
	else:
            os.system(VIEWER + PATH_PAUSEOPTION + "pause_resume.png")
    if position == "DOWN":
        if control_on() == True and os.path.isfile(PATH_PAUSEOPTION + romname + "_stop.png") == True :
            os.system(VIEWER + PATH_PAUSEOPTION + romname + "_stop.png")
	else:
            os.system(VIEWER + PATH_PAUSEOPTION + "pause_stop.png")
        
def is_running(pname):
    ps_grep = run_cmd("ps -ef | grep " + pname + " | grep -v grep")
    if len(ps_grep) > 1:
        return True
    else:
        return False
    
def kill_proc(name):
    ps_grep = run_cmd("ps -aux | grep " + name + "| grep -v 'grep'")
    if len(ps_grep) > 1: 
        os.system("killall " + name)

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

    global SELECT_BTN_ON, START_BTN_ON, PAUSE_MODE_ON
    global UP_ON, DOWN_ON, MENU_INDEX
    
    (js_time, js_value, js_type, js_number) = struct.unpack(event_format, event)

    # ignore init events
    if js_type & JS_EVENT_INIT:
        return False

    if js_type == JS_EVENT_AXIS and js_number <= 7:
        '''
        if js_number % 2 == 0:
            if js_value <= JS_MIN * JS_THRESH:
                print "Left pushed"
            if js_value >= JS_MAX * JS_THRESH:
                print "Right pushed"
        '''
        if js_number % 2 == 1:
            if js_value <= JS_MIN * JS_THRESH:
                #print "Up pushed"
                UP_ON = True
                DOWN_ON = False
                if PAUSE_MODE_ON == True:
                    MENU_INDEX = 1
                    change_viewer("UP")
                elif SELECT_BTN_ON == True:
                    print "OSD mode on"
            if js_value >= JS_MAX * JS_THRESH:
                #print "Down pushed"
                DOWN_ON = True
		UP_ON = False
                if PAUSE_MODE_ON == True:
                    MENU_INDEX = 2
                    change_viewer("DOWN")
                elif SELECT_BTN_ON == True:
                    print "OSD mode off"
                    stop_viewer()
	    if js_value == 0:
		UP_ON = False
		DOWN_ON = False
    
    if js_type == JS_EVENT_BUTTON:
        if js_value == 1:
            if js_number == btn_a:
                if PAUSE_MODE_ON == True:
                    if MENU_INDEX == 1:
                        print "Resume"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &")
                        PAUSE_MODE_ON = False
                    elif MENU_INDEX == 2:
                        print "Kill"
                        stop_viewer()
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGCONT &");
                        os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGINT");
                        close_fds(js_fds)
                        sys.exit(0)
            elif js_number == btn_select:
                SELECT_BTN_ON = True
            elif js_number == btn_start:
                START_BTN_ON = True
            else:
                return False
        elif js_value == 0:
            if js_number == btn_select:
                SELECT_BTN_ON = False
            elif js_number == btn_start:
                START_BTN_ON = False
            else:
                return False
        
        if SELECT_BTN_ON == True and START_BTN_ON == True:
            print "Select+Start Pushed"
            if PAUSE_MODE_ON == False:
                PAUSE_MODE_ON = True;
                MENU_INDEX = 1    # Resume
                stop_viewer()
                os.system("ps -ef | grep emulators | grep -v grep | awk '{print $2}' | xargs kill -SIGSTOP &");
                start_viewer()
                
    return True

def main():
    
    global btn_select, btn_start, btn_a, romname, system

    # Draw control images
    if control_on() == True:
        while True:
            if is_running("bin/retroarch") == False:
                time.sleep(1)    # wait for launching game
                continue
            else:
                break
        system = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $10}'").split("/")[4]
        romname = run_cmd("ps -ef | grep bin/retroarch | grep -v grep | awk '{print $13}'").split("/")[6][0:-5]
        if check_update() == True:
	    load_layout()
	    buttons = get_info()
            draw_picture(system, buttons)

    if os.path.isfile(PATH_PAUSEMENU + "button.cfg") == False:
        return False
    f = open(PATH_PAUSEMENU + "button.cfg", 'r')
    line = f.readline()
    words = line.split()
    btn_select = int(words[0])
    btn_start = int(words[1])
    btn_a = int(words[2])

    js_fds=[]
    rescan_time = time.time()
    while True:
        do_sleep = True
        if not js_fds:
            js_devs, js_fds = open_devices()
            if js_fds:
                i = 0
                current = time.time()
                js_last = [None] * len(js_fds)
                for js in js_fds:
                    js_last[i] = current
                    i += 1
            else:
                time.sleep(1)
        else:
            i = 0
            for fd in js_fds:
                event = read_event(fd)
                if event:
                    do_sleep = False
                    #if time.time() - js_last[i] > JS_REP:
                    if time.time() - js_last[i] > 0:                        
                        if process_event(event):
                            js_last[i] = time.time()
                elif event == False:
                    close_fds(js_fds)
                    js_fds = []
                    break
                i += 1

        if time.time() - rescan_time > 2:
            rescan_time = time.time()
            if cmp(js_devs, get_devices()):
                close_fds(js_fds)
                js_fds = []

        if do_sleep:
            time.sleep(0.01)

if __name__ == "__main__":
    import sys

    try:
        main()

    # Catch all other non-exit errors
    except Exception as e:
        sys.stderr.write("Unexpected exception: %s" % e)
        sys.exit(1)

    # Catch the remaining exit errors
    except:
        sys.exit(0)
