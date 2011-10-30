#!/bin/sh

# Copies all files (not en*.po as they are used for string change suggestions)
# from our translation repo into po/
# Requires a checkout of the UH translation repo with the following structure:
# (relative to the location of this file)
# ../../translations


TL_SOURCE='../translations'  #origin (TL repo pootle export)
TL_DIR='po/'  #destination
TL_REGEX='s,:,,g;s,.po,  ,g;s,alencia,,g;s,(../translations/uh/|messages|translations),\t,g;s/[.,]//g'
TL_TUT_REGEX='s,:,,g;s,.po,,g;s,alencia,,g;s,(../translations/uh-tutorial/|messages|translations),\t,g;s/[.,]//g'
TL_TUT_TEMPDIR='po/po_temp_tutorial/'
TUT_NOT_SHIPPING=(en-suggest)

function build_tl_tut_ungrep {
	c='grep -v -e en.po'
	for i in "${TUT_NOT_SHIPPING[@]}"; do
		c+=" -e $i.po "
	done
	TL_TUT_UNGREP="$c"
}

function tl_check {
	# tells us which translations meet shipping criteria
	msgfmt --check-format --statistics -o /dev/null $1 -v 2>&1 |perl -npe "$TL_REGEX"
	return 3
}
function tl_tut_check {
	# tells us which tutorial translations meet shipping criteria
	msgfmt --check-format --statistics -o /dev/null $1 -v 2>&1 |perl -npe $TL_TUT_REGEX
	return 3
}




for file in $(ls $TL_SOURCE/uh/*.po |grep -v -e en.po -e en-suggest.po); do
	tl_check $file
	if [ $? -ne 3 ]; then
		echo '  !!This file seems to be broken. Skipping.'
		#which means that msgfmt found critical errors. Fix ASAP!
	else
		cp $file $TL_DIR
	fi
done;
echo 'Main translation files copied.'
echo '=============================='
echo

if [ ! -d $TL_TUT_TEMPDIR ] ; then
	mkdir $TL_TUT_TEMPDIR
fi

build_tl_tut_ungrep

rm -rf "$TL_TUT_TEMPDIR/en-suggest.po"
for tutfile in $(ls $TL_SOURCE/uh-tutorial/*.po |$TL_TUT_UNGREP); do
	#tl_tut_check $tutfile
	#if [ $? -ne 3 ]; then
	#	echo '  !!This file has not enough content or is broken. Skipping.'
		#which means that less than 40% of the strings are completed (unfuzzy)
	#else
		rm -rf "$TL_TUT_TEMPDIR/$tutfile"
		cp $tutfile $TL_TUT_TEMPDIR
	#fi
done;

INCOMPLETE=( bg  ca@valencia  cs  da  et  hu  lt  nb  pt_BR  sl)
echo 'Removing these tutorial translations:'
for file in ${INCOMPLETE[@]}; do
	tl_tut_check "$TL_TUT_TEMPDIR/$file.po" | perl -npe 's,(po_temp_tutorial//|messages|translations),\t,g'
	rm "$TL_TUT_TEMPDIR/$file.po"
done

sh ./development/create_scenario_pot.sh tutorial $TL_TUT_TEMPDIR
