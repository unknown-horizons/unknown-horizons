#!/bin/sh

# script to convert path images from wentam's structure to UH structure


if [ $# -ne 5 ] ; then
	echo "USAGE: $0 <source-dir> <target-dir> <action-set-name> <object-id> <settler-level>"
	exit 1
fi

S=$1
T=$2
ACTION_SET_NAME=$3
OBJECT_ID=$4
SETTLER_LEVEL=$5

function _mk_dirs() {
	mkdir $1
	mkdir $1/45 $1/135 $1/225 $1/315
}

function do_cp() {
	for i in a b c d ab ac ad bc bd cd abc abd acd bcd abcd; do
		_mk_dirs "$T/$i"
	done

	cp $S/crossing/45/0.png $T/abcd/45/
	cp $S/crossing/45/0.png $T/abcd/135/
	cp $S/crossing/45/0.png $T/abcd/225/
	cp $S/crossing/45/0.png $T/abcd/315/
	
	cp $S/curve/* -r $T/ab

	cp $S/curve/135/0.png $T/ad/45
	cp $S/curve/225/0.png $T/ad/135
	cp $S/curve/315/0.png $T/ad/225
	cp $S/curve/45/0.png $T/ad/315

	cp $S/curve/315/0.png $T/bc/45
	cp $S/curve/45/0.png $T/bc/135
	cp $S/curve/135/0.png $T/bc/225
	cp $S/curve/225/0.png $T/bc/315

	cp $S/curve/225/0.png $T/cd/45
	cp $S/curve/315/0.png $T/cd/135
	cp $S/curve/45/0.png $T/cd/225
	cp $S/curve/135/0.png $T/cd/315
	
	cp $S/straight/45/0.png $T/ac/315
	cp $S/straight/45/0.png $T/ac/135
	cp $S/straight/135/0.png $T/ac/45
	cp $S/straight/135/0.png $T/ac/225

	cp $S/straight/135/0.png $T/bd/135
	cp $S/straight/135/0.png $T/bd/315
	cp $S/straight/45/0.png $T/bd/45
	cp $S/straight/45/0.png $T/bd/225

	cp $S/turning/45/0.png $T/abc/45
	cp $S/turning/135/0.png $T/abc/135
	cp $S/turning/225/0.png $T/abc/225
	cp $S/turning/315/0.png $T/abc/315

	cp $S/turning/45/0.png $T/abd/315
	cp $S/turning/135/0.png $T/abd/45
	cp $S/turning/225/0.png $T/abd/135
	cp $S/turning/315/0.png $T/abd/225

	cp $S/turning/45/0.png $T/acd/225
	cp $S/turning/135/0.png $T/acd/315
	cp $S/turning/225/0.png $T/acd/45
	cp $S/turning/315/0.png $T/acd/135

	cp $S/turning/45/0.png $T/bcd/135
	cp $S/turning/135/0.png $T/bcd/225
	cp $S/turning/225/0.png $T/bcd/315
	cp $S/turning/315/0.png $T/bcd/45

	# hmm.. acab is still missing..

	cp $S/deadend/* -r $T/d

	cp $S/deadend/45/0.png $T/b/225
	cp $S/deadend/135/0.png $T/b/315
	cp $S/deadend/225/0.png $T/b/45
	cp $S/deadend/315/0.png $T/b/135
	
	cp $S/deadend/45/0.png $T/c/315
	cp $S/deadend/135/0.png $T/c/45
	cp $S/deadend/225/0.png $T/c/135
	cp $S/deadend/315/0.png $T/c/225

	cp $S/deadend/45/0.png $T/a/135
	cp $S/deadend/135/0.png $T/a/225
	cp $S/deadend/225/0.png $T/a/315
	cp $S/deadend/315/0.png $T/a/45

}


function create_sqls() {
	echo "--------- BEGIN SQL ----------"

	# action set
	echo "INSERT INTO \"action_set\" VALUES('${ACTION_SET_NAME}',NULL,${OBJECT_ID},${SETTLER_LEVEL});"
	echo "--------- END SQL ------------"
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
