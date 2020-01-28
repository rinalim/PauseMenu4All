import sys, os, time
import xml.etree.ElementTree as ET
from subprocess import *
import ast

ES_INPUT = '/opt/retropie/configs/all/emulationstation/es_input.cfg'
CONFIG_DIR = '/opt/retropie/configs/'
RETROARCH_CFG = CONFIG_DIR + 'all/retroarch.cfg'
PATH_PAUSEMENU = CONFIG_DIR + 'all/PauseMenu4All/'	
PATH_PAUSEOPTION = PATH_PAUSEMENU+'control/'

retroarch_key = {}
user_key = {}
key_map = {}
turbo_key = ''

capcom_dd = ['ddtod', 'ddsom']

sys_map = {
    "lr-fbneo": "FinalBurn Neo",
    "lr-fbalpha": "FB Alpha"
}

def run_cmd(cmd):
# runs whatever in the cmd variable
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

def load_layout():

    global retroarch_key

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

    retroarch_key = ast.literal_eval(f.readline())
    f.close()

def set_keymap(romname, layout_index):
    
    global turbo_key
    
    if layout_index[2] == '2':    # capcom fighting game
        if layout_index[0] == '1':
            key_map['1'] = user_key['1']     # LP
            key_map['9'] = user_key['2']     # MP
            key_map['10'] = user_key['3']    # HP
            key_map['0'] = user_key['4']     # LK
            key_map['8'] = user_key['5']     # MK
            key_map['11'] = user_key['6']    # HK
        elif layout_index[0] == '2':
            key_map['1'] = user_key['4']
            key_map['9'] = user_key['5']
            key_map['10'] = user_key['6']
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['11'] = user_key['3']
    elif romname in capcom_dd:
        if layout_index[0] == '1':
            key_map['0'] = user_key['4']    # A
            key_map['8'] = user_key['5']    # B
            key_map['1'] = user_key['2']    # C
            key_map['9'] = user_key['1']    # D
        elif layout_index[0] == '2':
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['1'] = user_key['5']
            key_map['9'] = user_key['4']
        elif layout_index[0] == '3':
            key_map['0'] = user_key['4']
            key_map['8'] = user_key['5']
            key_map['1'] = user_key['1']
            key_map['9'] = user_key['6']
    else:
        if layout_index[0] == '1':
            key_map['0'] = user_key['4']    # A
            key_map['8'] = user_key['5']    # B
            key_map['1'] = user_key['1']    # C
            key_map['9'] = user_key['2']    # D
        elif layout_index[0] == '2':
            key_map['0'] = user_key['1']
            key_map['8'] = user_key['2']
            key_map['1'] = user_key['4']
            key_map['9'] = user_key['5']
        elif layout_index[0] == '3':
            key_map['0'] = user_key['4']
            key_map['8'] = user_key['5']
            key_map['1'] = user_key['6']
            key_map['9'] = user_key['1']
        elif layout_index[0] == '4':
            key_map['0'] = user_key['4'] + user_key['5']
            key_map['8'] = user_key['1']
            key_map['1'] = user_key['2']
            turbo_key = retroarch_key[user_key['5']]
        elif layout_index[0] == '5':
            key_map['0'] = user_key['1'] + user_key['2'] 
            key_map['8'] = user_key['4']
            key_map['1'] = user_key['5']
            turbo_key = retroarch_key[user_key['2']]
        elif layout_index[0] == '6':
            key_map['0'] = user_key['4'] + user_key['1'] 
            key_map['8'] = user_key['5'] + user_key['2'] 
            key_map['1'] = user_key['6'] + user_key['3']
            turbo_key = retroarch_key[user_key['1']]


def update_fba_rmp(system, romname, index):

    if os.path.isdir('/opt/retropie/configs/fba/'+sys_map[system]) == False:
        run_cmd('mkdir /opt/retropie/configs/fba/'+sys_map[system].replace(" ","\ "))
    buf = ''
    run_cmd("sed -i \'/input_player" + str(index) + "/d\' /opt/retropie/configs/fba/"+sys_map[system].replace(" ","\ ") + '/'  + romname + ".rmp")
    f = open('/opt/retropie/configs/fba/'+sys_map[system] + '/' + romname + '.rmp', 'a')
    for key in key_map:
        res = 'input_player' + str(index) + '_btn_' + key_map[key][0] + ' = ' + '\"' + key + '\"'
        buf += res + '\n'
        if len(key_map[key]) == 2:
            res = 'input_player' + str(index) + '_btn_' + key_map[key][1] + ' = ' + '\"' + key + '\"'
            buf += res + '\n'
    f.write(buf)
    f.close()
    run_cmd("sed -i \'/input_player" + str(index) + "_turbo_btn/d\' /home/pi/RetroPie/roms/fba/" + romname + ".zip.cfg")
    run_cmd("echo 'input_player" + str(index) + "_turbo_btn = " + turbo_key + "' >> /home/pi/RetroPie/roms/fba/" + romname + ".zip.cfg")

    if os.path.isdir('/home/pi/.config/retroarch/config/remaps') == True:
        run_cmd('cp -r /opt/retropie/configs/fba/FinalBurn\ Neo/' + romname + '.rmp /home/pi/.config/retroarch/config/remaps/FinalBurn\ Neo/')

if __name__ == "__main__":

    system = sys.argv[1]
    romname = sys.argv[2]
    layout_index = sys.argv[3]
    load_layout()
    set_keymap(romname, layout_index)
    update_fba_rmp(system, romname, 1)
