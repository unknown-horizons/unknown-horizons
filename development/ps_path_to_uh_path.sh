#!/bin/sh

# script to convert path images from wentam's structure to UH structure


if [ $# -ne 5 ] ; then
	echo "USAGE: $0 <source-dir> <target-dir> <action-set-id> <action-set-name> <next-animation-id>"
	exit 1
fi

S=$1
T=$2
ACTION_SET_ID=$3
ACTION_NAME=$4
ANIM_ID=$5

# TODO: gravel_to_dirt

function do_cp() {
	cp $S/crossing/45/0.png $T/abcd.png

	cp $S/curve/45/0.png $T/ab.png
	cp $S/curve/135/0.png $T/ad.png
	cp $S/curve/225/0.png $T/cd.png
	cp $S/curve/315/0.png $T/bc.png

	cp $S/deadend/45/0.png $T/d.png
	cp $S/deadend/135/0.png $T/c.png
	cp $S/deadend/225/0.png $T/b.png
	cp $S/deadend/315/0.png $T/a.png

	cp $S/straight/45/0.png $T/bd.png
	cp $S/straight/135/0.png $T/ac.png
	
	cp $S/turning/45/0.png $T/abc.png
	cp $S/turning/135/0.png $T/abd.png
	cp $S/turning/225/0.png $T/acd.png
	cp $S/turning/315/0.png $T/bcd.png
}

function create_sqls() {
	echo "------- BEGIN SQL ----------"

	# action set
	echo "INSERT INTO \"action_set\" VALUES('${ACTION_NAME}',NULL,${ACTION_SET_ID},0);"

	# animations
	ANIM_ID_ITER=$ANIM_ID
	REL_PATH="content${T##*content}"
	for i in a ab abc abcd abd ac acd ad b bc bcd bd c cd d; do
		echo "INSERT INTO \"animation\" VALUES(${ANIM_ID_ITER},'${REL_PATH}/${i}.png',0.0);"
		let "ANIM_ID_ITER += 1"
	done

	# actions
	cat <<EOF
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 45, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 315, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 225, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 135, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ac', 45, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ac', 315, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ac', 225, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ac', 135, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bd', 45, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bd', 315, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bd', 225, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bd', 135, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'a', 45, $((0+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'a', 315, $((8+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'a', 225, $((12+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'a', 135, $((14+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'c', 45, $((12+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'c', 315, $((14+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'c', 225, $((0+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'c', 135, $((8+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'b', 45, $((8+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'b', 315, $((12+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'b', 225, $((14+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'b', 135, $((0+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'd', 45, $((14+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'd', 315, $((0+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'd', 225, $((8+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'd', 135, $((12+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ab', 45, $((1+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ab', 315, $((9+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ab', 225, $((13+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ab', 135, $((7+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bc', 45, $((9+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bc', 315, $((13+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bc', 225, $((7+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bc', 135, $((1+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'cd', 45, $((13+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'cd', 315, $((7+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'cd', 225, $((1+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'cd', 135, $((9+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ad', 45, $((7+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ad', 315, $((1+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ad', 225, $((9+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'ad', 135, $((13+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abcd', 45, $((3+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abcd', 315, $((3+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abcd', 225, $((3+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abcd', 135, $((3+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bcd', 45, $((10+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bcd', 315, $((6+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bcd', 225, $((4+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'bcd', 135, $((2+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'acd', 45, $((6+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'acd', 315, $((4+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'acd', 225, $((2+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'acd', 135, $((10+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abd', 45, $((4+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abd', 315, $((2+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abd', 225, $((10+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abd', 135, $((6+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abc', 45, $((2+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abc', 315, $((10+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abc', 225, $((6+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'abc', 135, $((4+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 45, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 315, $((11+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 225, $((5+$ANIM_ID)));
INSERT INTO "action" VALUES(${ACTION_SET_ID}, 'default', 135, $((11+$ANIM_ID)));
EOF

	echo "------- END SQL ----------"
}


echo -n "copy files? [y/n] "
read ans
if [ "$ans" == "y" ]; then
	do_cp
fi
echo -n "create sql? [y/n] "
read ans
if [ "$ans" = "y" ] ; then
	create_sqls
fi
