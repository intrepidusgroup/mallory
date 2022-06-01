#!/bin/bash
# ----------------------------------------------------------------
# This script updates a basic installation of Ubuntu (10.10 or 11.04)
# to the latest package revs, and installs the packages required
# to run the current (1.0) version of the Mallory tool.
# ----------------------------------------------------------------
# Copyright 2011 - Intrepidus Group
# ----------------------------------------------------------------
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ----------------------------------------------------------------

set -e
export UPDATE_DIR=${HOME}/.mallory/update
export UPDATE_LOG=${UPDATE_DIR}/update.log

# -----------------------------------------------------------------
# functions
# -----------------------------------------------------------------
function print_header {
  echo "+--------------------------------------------------------+"
  echo "|           MALLORY  INSTALL/UPDATE  SCRIPT              |"
  echo "+--------------------------------------------------------+"
}

function phase0 {
  # create the update directory if it doesn't exist
  mkdir -p ${UPDATE_DIR}
  print_header
  echo "| Before running this script, please ensure that you've  |"
  echo "|  configured a network interface and that the internet  |"
  echo "|         is reachable by this virtual machine.          |"
  echo "+--------------------------------------------------------+"
  echo "| Once you have done this (or if you already had) simply |"
  echo "|        rerun this script to continue the update        |"
  echo "+--------------------------------------------------------+"
  echo "phase1" > ${UPDATE_DIR}/.next_phase
  exit 0
}

function phase1 {
  print_header
  echo "beginning Mallory installation"
  echo "updating apt package list"
  sudo apt-get update |tee ${UPDATE_LOG}
  echo ""

  echo "upgrading OS to latest versions of installed packages"
  sudo apt-get upgrade -y |tee -a ${UPDATE_LOG}

  echo "installing Mallory dependencies"
  sudo apt-get -y install build-essential libnetfilter-conntrack-dev libnetfilter-conntrack3 |tee -a ${UPDATE_LOG}
  if [ ! -f /usr/lib/netfilter_conntrack.so.1 ]; then
    sudo ln -s /usr/lib/libnetfilter_conntrack.so /usr/lib/libnetfilter_conntrack.so.1
  fi
  sudo apt-get -y install python-pip git python-m2crypto python-qt4 pyro-gui python-netfilter python-pyasn1 python-pil python-ipy|tee -a ${UPDATE_LOG}
  sudo apt-get -y install python-paramiko python-twisted-web python-qt4-sql libqt4-sql-sqlite sqlite3 |tee -a ${UPDATE_LOG}
  sudo pip install pynetfilter_conntrack
  echo ""

  echo "enter directory you'd like Mallory to be installed to"
  read -p "(default: ${HOME}/mallory)" mallorydir

  if [ "$mallorydir" == "" ]; then
    mallorydir="${HOME}/mallory";
  fi
  mkdir -p $mallorydir
  echo ${mallorydir} > ${UPDATE_DIR}/installdir
  echo "retrieving current mallory source from bitbucket"
  /usr/bin/git clone https://github.com/intrepidusgroup/mallory ${mallorydir}/current

  echo "phase2" > ${UPDATE_DIR}/.next_phase
  phase2
}


function phase2 {
  print_header
  echo "Mallory installation completed"
  echo "To use mallory:"
  echo "Open a new terminal window, cd to ${mallorydir}/current/src, then run:"
  echo "  sudo python ./mallory.py"
  echo ""
  echo "To run the mallory GUI:"
  echo "Open a new terminal window cd to ${mallorydir}/current/src and run:"
  echo "  sudo chown $USER mallory.log"
  echo " where $USER is the user you are logged in as. Then run:"
  echo "  python ./launchgui.py"
  echo "Have fun!"
  read -n1 -p "press any key to continue..."

  echo "update" > ${UPDATE_DIR}/.next_phase
  exit 0
}

function update {
  echo 'Please cd into ${mallorydir}/current and update manually with "git pull"'
  echo "If you want to rerun this script please clean ~/.mallory/update"
  exit 0
}


# -----------------------------------------------------------------
# scriptybits
# -----------------------------------------------------------------

if [[ -f ${UPDATE_DIR}/.next_phase ]]; then
  case `cat ${UPDATE_DIR}/.next_phase` in
    phase0)
      phase0
    ;;

    phase1)
      phase1
    ;;

    phase2)
      phase2
    ;;

    update)
      update
    ;;

    phase4)
      echo "phase4: profit!"
      exit 0
    ;;

    *)
      echo "unknown update status, attempting update"
      update
    ;;
  esac
else
  phase0
fi
