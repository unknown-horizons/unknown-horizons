#!/bin/bash

# ###################################################
# Copyright (C) 2012 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

if [ ! `which dialog 2>/dev/null` ] ; then
	echo "Error: You need the program 'dialog' to run this script."
	exit 1
fi

clear
dialog --title "Info" --yesno "This script will download and compile fife and Unknown Horizons. Do you want to proceed?" 8 40

if [ "$?" = 1 ]; then
	exit 0
else
	## The installer itself
	distro="Unknown"
	lsbinfo="Description:[[:space:]]*([^ ]*)"
	lsbfile="/etc/(.*)[-_]"

	if [ `which lsb_release 2>/dev/null` ]; then
		distro=`lsb_release -d`
		if [[ $distro =~ $lsbinfo ]]; then
			distro=${BASH_REMATCH[1]}
		else
			echo "Couldn't find distribution information in lsb output"
			exit 1
		fi

	else
		etcFiles=`ls /etc/*[-_]{release,version} 2>/dev/null`
		for file in $etcFiles; do
			if [[ $file =~ $lsbfile ]]; then
				distro=${BASH_REMATCH[1]}
				break
			else
				echo "Couldn't detect your distribution"
				exit 1
			fi
		done
	fi

	distro=`echo $distro | tr "[:upper:]" "[:lower:]"`

	case $distro in
		suse)
		distro="opensuse"
		;;
		linux)
		distro="linuxmint"
		;;
	esac


	## Install dependencies
	case "$distro" in
	"debian")
		dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
		clear
		su -c "apt-get install build-essential scons libalsa-ocaml-dev libsdl1.2-dev libboost-dev libsdl-ttf2.0-dev libsdl-image1.2-dev libvorbis-dev libalut-dev python2.6 python-dev libboost-regex-dev libboost-filesystem-dev libboost-test-dev swig zlib1g-dev libopenal-dev subversion python-yaml libxcursor1 libxcursor-dev python-distutils-extra git-core"
		if [ $? -ne 0 ] ; then
			echo "Error: Failed to install required dependencies"
			exit 1
		fi
		;;
	"ubuntu")
		dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
		clear
		sudo apt-get install -y build-essential scons libalsa-ocaml-dev libsdl1.2-dev libboost-dev libsdl-ttf2.0-dev libsdl-image1.2-dev libvorbis-dev libalut-dev python2.6 python-dev libboost-regex-dev libboost-filesystem-dev libboost-test-dev swig zlib1g-dev libopenal-dev subversion python-yaml libxcursor1 libxcursor-dev python-distutils-extra git-core
		if [ $? -ne 0 ] ; then
			echo "Error: Failed to install required dependencies"
			exit 1
		fi
		;;
	"crunchbang")
		dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
		clear
		sudo apt-get install -y build-essential scons libalsa-ocaml-dev libsdl1.2-dev libboost-dev libsdl-ttf2.0-dev libsdl-image1.2-dev libvorbis-dev libalut-dev python2.6 python-dev libboost-regex-dev libboost-filesystem-dev libboost-test-dev swig zlib1g-dev libopenal-dev subversion python-yaml libxcursor1 libxcursor-dev python-distutils-extra git git-core
		if [ $? -ne 0 ] ; then
			echo "Error: Failed to install required dependencies"
			exit 1
		fi
		;;
	"gentoo")
		dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
		clear
		su -c "emerge --ask --noreplace libvorbis libogg media-libs/openal guichan boost libsdl sdl-image sdl-ttf scons subversion pyyaml python-distutils-extra intltool git git-core"
		if [ $? -ne 0 ] ; then
			echo "Error: Failed to install required dependencies"
			exit 1
		fi
		;;
	*)
		dialog --msgbox "Error! Your distribution is unsupported or could not be detected." 8 50
		exit 0
		;;
	esac


	## Create needed directories, make svn checkouts of fife and unknown horizons
	tmpfile=`tempfile`
	dialog --inputbox "Select a directory to create the Fife and Unknown-Horizons folders." 0 0 2> "$tmpfile"
	clear
	echo "Please wait while download is initiated..."
	cd `cat "$tmpfile"`
	if [ $? -ne 0 ] ; then
		echo "Error: You entered an invalid directory"
		exit 1
	fi
	FOLDER=`cat "$tmpfile"`
	rm -f "$tmpfile"
	mkdir fife
	mkdir unknown-horizons
	cd fife
	svn co http://fife.svn.cvsdude.com/engine/trunk
	cd trunk
	scons -c && scons ext && scons fife-python
	cd ../..
	git clone git://github.com/unknown-horizons/unknown-horizons.git
fi

dialog --title "You successfully installed Fife and Unknown-Horizons" --yesno "Do you want to run Unknown Horizons now?" 5 28
if [ "$?" = 1 ]; then
	clear
	echo "Have fun with playing Unknown-Horizons!"
	echo "In the future you can run UH via: cd $FOLDER/unknown-horizons/ && python ./run_uh.py"
	echo "Hit return to exit."
	read
	clear
	exit 0
else
	cd unknown-horizons
	python ./run_uh.py
	echo "In the future you can run UH via: cd $FOLDER/unknown-horizons/ && python ./run_uh.py"
	echo "Hit return to exit."
	read
fi
clear
exit 0
