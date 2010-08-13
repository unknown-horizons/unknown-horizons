#!/bin/bash

# ###################################################
# Unknown Horizons Installer
# ###################################################

clear
dialog --title "This script will download and Compile fife + Unknown Horizons" --yesno "Do you want to proceed?" 5 28
if [ "$?" = 1 ]; then
	exit 0
else
	## The installer itself
	dialog --title "Wich Distribution is yours?" --menu \
		"Select your Distribution" \
		11 40 4  \
		"1" "Debian" \
		"2" "Ubuntu" \
		"3" "Gentoo" 2>/tmp/h.out
	SEL="`cat /tmp/h.out`"

	## Install dependencies
	case "$SEL" in
		1)
			dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
			clear
			su
			apt-get install build-essential scons libalsa-ocaml-dev libsdl1.2-dev libboost-dev libsdl-ttf2.0-dev libsdl-image1.2-dev libvorbis-dev libalut-dev python2.6 python-dev libboost-regex-dev libboost-filesystem-dev libboost-test-dev swig zlib1g-dev libopenal-dev subversion python-yaml libxcursor1 libxcursor-dev python-distutils-extra
			;;
		2)
        		dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
        		clear
			sudo apt-get install -y build-essential scons libalsa-ocaml-dev libsdl1.2-dev libboost-dev libsdl-ttf2.0-dev libsdl-image1.2-dev libvorbis-dev libalut-dev python2.6 python-dev libboost-regex-dev libboost-filesystem-dev libboost-test-dev swig zlib1g-dev libopenal-dev subversion python-yaml libxcursor1 libxcursor-dev python-distutils-extra 
			;;
		3)
                        dialog --msgbox "Now enter your root password to install the build dependencies for Fife and Unknown-Horizons" 8 60
                        clear
                        su
                        emerge --ask --noreplace libvorbis libogg media-libs/openal guichan boost libsdl sdl-image sdl-ttf scons subversion pyyaml python-distutils-extra intltool
                        ;;
                *)
                	dialog --msgbox "Error you didn't select a distribution!" 8 50
                	exit 0
                	;;
	esac

	dialog --inputbox "Select a directory to create the Fife and Unknown-Horizons folders." 0 0 2> /tmp/h.out
	cd `cat /tmp/h.out`
	FOLDER=`cat /tmp/h.out`
	mkdir fife
	mkdir unknown-horizons
	cd fife
	svn co http://fife.svn.cvsdude.com/engine/trunk
	cd trunk
	scons ext && scons
	cd ../../unknown-horizons
	svn co svn://unknown-horizons.org/unknown-horizons/trunk
fi

dialog --title "You successfully installed Fife and Unknown-Horizons" --yesno "Do you want to run Unknown Horizons now?" 5 28
if [ "$?" = 1 ]; then
	clear
	echo "Have fun with playing Unknown-Horizons!"
	read
	clear
        exit 0
else
	cd trunk
	python ./run_uh.py
	echo "In the future you can run uh via: cd $FOLDER/unknown-horizons/trunk && python ./run_uh.py"
	read
fi
clear
exit 0
