rm -rf /opt/retropie/configs/all/PauseMenu4All/

sudo sed -i '/PauseMenu4All.py/d' /opt/retropie/configs/all/runcommand-onstart.sh

python ./PauseMenu4All/remove.py
