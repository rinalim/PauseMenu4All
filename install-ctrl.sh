# Reference    :
# https://github.com/RetroPie/RetroPie-Setup/blob/master/scriptmodules/supplementary/runcommand/joy2key.py
# https://github.com/sana2dang/PauseMode

sudo apt-get install libjpeg8 -y
sudo apt-get install imagemagick -y
sudo apt-get install fonts-nanum -y
sudo apt-get install fonts-nanum-extra -y

rm -rf /opt/retropie/configs/all/PauseMenu4All/
mkdir /opt/retropie/configs/all/PauseMenu4All/
cp -f -r ./PauseMenu4All /opt/retropie/configs/all/

sudo sed -i '/PauseMenu4All.py/d' /opt/retropie/configs/all/runcommand-onstart.sh
echo '/usr/bin/python /opt/retropie/configs/all/PauseMenu4All/PauseMenu4All.py /dev/input/js0 -control &' >> /opt/retropie/configs/all/runcommand-onstart.sh

chgrp -R -v pi /opt/retropie/configs/all/PauseMenu4All/
chown -R -v pi /opt/retropie/configs/all/PauseMenu4All/

python ./PauseMenu4All/setup.py /dev/input/js0 -control
