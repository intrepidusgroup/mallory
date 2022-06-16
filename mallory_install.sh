#!/bin/bash
echo -e "Latest supported Debian-based releases are Ubuntu 18.04 (Bionic) or Debian 10 (Buster).\nOnly Python 2 is supported.\nThis script assumes the use of apt package manager.\nIt is recommended to install mallory in a virtual machine.\nThis script was tested on ubuntu; there may be a variance in package names between distributions."
echo
echo "The script will now install/update dependencies using apt and pip. (safe to rerun)"
read -p "Press any key to continue, or ctrl+c to exit: " -n 1 -r
echo 

set -e
set -x
sudo apt-get update

sudo apt-get install build-essential libnetfilter-conntrack-dev git python-pip python-m2crypto python-qt4 pyro-gui python-netfilter python-pyasn1 python-pil python-ipy python-paramiko python-twisted-web python-qt4-sql libqt4-sql-sqlite sqlite3 python  --no-install-recommends

sudo -H pip2 install pynetfilter_conntrack
set +x

echo
echo 'Installation complete.'
echo 
echo "If you haven't already, install the Mallory repo by running in a directory of your choosing:"
echo 
echo "    /usr/bin/git clone https://github.com/Tokarak/mallory"
echo 
echo 'In the repo, src/mallory.py has the core functionality of mallory. src/launchgui.py can launch the gui WHILE src/mallory.py is already running.'
echo 'It is recommended to run the gui on your virtual machine using ssh with X11 forwarding (ssh -X ...) instead of installing a bulky desktop. To enable X11forwarding on your VM:'
echo "    sudo apt install xauth"
echo 'Search "X11Forwarding" online to learn more.'
echo
echo 'Notice: if you get a "cannot open shared object file" error on running the script, please see:'
echo 'https://web.archive.org/web/20131007182424/http://intrepidusgroup.com/insight/2013/07/getting-mallory-to-run-in-modern-versions-of-ubuntu/'
echo "Script end."
echo
exit 0