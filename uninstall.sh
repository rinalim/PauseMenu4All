rm -rf /opt/retropie/configs/all/PauseMenu/

sudo sed -i '/PauseMenu.py/d' /opt/retropie/configs/all/runcommand-onstart.sh

python ./PauseMenu/remove.py
