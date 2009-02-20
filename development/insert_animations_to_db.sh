#!/bin/bash

if ! ls content >/dev/null 2>&1; then
	echo "please call from unknown-horizons root directory"
	exit 1
fi

echo "works currently only for animated movement"
echo

if [ $# -ne 3 ] ; then
	echo "USAGE: $0 animation_id_base action_set_id directory"
	echo "EXAMPLE: $0 2 3 content/gfx/units/herder/walking_empty"
	exit
fi

animation_id=$(($1))
action_set_id=$2
dir=$3


if [ $animation_id -eq 0 ] ; then
	echo 'invalid animation id'
	exit 1
fi

if ! [ -d "$dir" ]; then
	echo 'invalid dir'
	exit 1
fi

frames=`find "$dir" -name *.png | wc -l`
action=`basename $dir`
echo "found $frames frames"
echo "action: $action"
echo -n "rotations: "
ls $dir

echo -n "proceed? (y|n) ";
read ans
if [ "$ans" != "y" ] ; then
	echo "Exiting."
	exit 1
fi
echo


ls $dir | while read rotation; do
	cur_dir=${dir}/${rotation}

	frames=`ls ${cur_dir}/*.png | wc -l`

	frame_length_diff=`echo "scale=3; 1/$frames" | bc`

	frame_length=0

	sql2="INSERT INTO action(action_set_id, action, rotation, animation_id) VALUES(\"$action_set_id\", \"$action\", \"$rotation\", \"$animation_id\")"

	echo $sql2

	ls ${cur_dir}/*.png | while read img_file ; do

		sql1="INSERT INTO animation(animation_id, file, frame_length) VALUES(\"$animation_id\", \"$img_file\", \"$frame_length\");"
		echo $sql1


		frame_length=`echo "scale=3; $frame_length+$frame_length_diff" | bc`

	done

	let "animation_id++"
done
