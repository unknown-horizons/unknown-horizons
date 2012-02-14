#!/bin/sh

###############################################################################
# Copies all files (not en*.po as they are used for string change suggestions)
# from our translation repo into po/
# Requires a checkout of the UH translation repo with the following structure:
# (relative to the location of this file)
# ../../translations
# Only run from UH directory of a git clone (where run_uh.py and the po/ folder
# are loacted)!


TL_SOURCE='../translations'  #origin (TL repo pootle export)
TL_DIR='po/'  #destination
TL_REGEX='s,:,,g;s,.po,  ,g;s,alencia,,g;s,(../translations/uh/|messages|message|translations),\t,g;s/[.,]//g'
TL_TUT_REGEX='s,:,,g;s,.po,,g;s,alencia,,g;s,(../translations/uh-tutorial/|messages|message|translations),\t,g;s/[.,]//g'
TL_TUT_TEMPDIR='po/po_temp_tutorial/'
TL_NOT_SHIPPING=(en-suggest) # languages that will never end up in UH (helpers)

# remove languages from INCOMPLETE if you see that their stats are similar or
# better numbers than included languages.  statistics are always printed,
# regardless of whether the language was considered INCOMPLETE or not.
# languages that would show up if more strings are translated:
TL_INCOMPLETE=( af  el  ga  gl  id  ko  lv  sr  th  tr  vi  zh_CN  zu )
TL_TUT_INCOMPLETE=( af  ca@valencia  el  ga  gl  id  ko  lt  lv  nb  sl  sr  th  tr  vi  zh_CN  zu )
###############################################################################

# this returns a string like the following:
#   'grep -v -e en.po -e en-suggest.po -e de.po'
# which means that en, en-suggest and de will not be considered when updating.
# Use the _INCOMPLETE variables above to adjust (e.g. because new interface
# translation maintainers are now working on the respective files).
function build_ungrep {
	c='grep -v -e en.po'
	for i in "${TL_NOT_SHIPPING[@]}"; do
		c+=" -e $i.po "
	done
	TL_TUT_UNGREP="$c"

	d='grep -v -e en.po'
	for i in "${TL_INCOMPLETE[@]}"; do
		d+=" -e $i.po "
	done
	for i in "${TL_NOT_SHIPPING[@]}"; do
		d+=" -e $i.po "
	done
	TL_UNGREP="$d"
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


if [ ! -d $TL_SOURCE ] ; then
	echo '!! No translation repository found. Tried here:'
	echo $TL_SOURCE
	echo '=> Please make sure you have a proper clone of the Unknown Horizons'
	echo '   translation export repository in that location.'
	echo '=> If you do not, run the following command in the current working dir:'
	echo '   git clone git://github.com/unknown-horizons/translations.git ../translations'
	exit 1 # stop executing script, no sense in trying to copy nonexistant files
fi

build_ungrep

echo '=> Removing these interface translations:'
for file in ${TL_INCOMPLETE[@]}; do
	tl_check "$TL_SOURCE/uh/$file.po" | perl -npe "$TL_REGEX"
done

echo
echo '=> Copying these interface translations:'

INTERFACE_FILES=$(ls $TL_SOURCE/uh/*.po -1 | $TL_UNGREP)
for file in $INTERFACE_FILES; do
	tl_check $file
	if [ $? -ne 3 ]; then
		echo '  !!This file seems to be broken. Skipping.'
		#which means that msgfmt found critical errors. Fix ASAP!
	else
		cp $file $TL_DIR
	fi
done;

echo
echo '=> Interface translation files copied.'
echo '   To compile them, run   setup.py build_i18n'
echo
echo
echo '=> Checking tutorial translations:'

if [ ! -d $TL_TUT_TEMPDIR ] ; then
	mkdir $TL_TUT_TEMPDIR
fi

rm -rf "$TL_TUT_TEMPDIR/en-suggest.po"
for tutfile in $(ls $TL_SOURCE/uh-tutorial/*.po |$TL_TUT_UNGREP); do
	#tl_tut_check $tutfile
	#if [ $? -ne 3 ]; then
	#	echo '  !!This file has not enough content or is broken. Skipping.'
		#which means that less than 33% of the strings are completed (unfuzzy)
	#else
		rm -rf "$TL_TUT_TEMPDIR/$tutfile"
		cp $tutfile $TL_TUT_TEMPDIR
	#fi
done;

echo '=> Removing these tutorial translations:'
for file in ${TL_TUT_INCOMPLETE[@]}; do
	tl_tut_check "$TL_TUT_TEMPDIR/$file.po" | perl -npe 's,(po_temp_tutorial//|messages|message|translations),\t,g'
	rm "$TL_TUT_TEMPDIR/$file.po"
done

sh ./development/create_scenario_pot.sh tutorial $TL_TUT_TEMPDIR
echo
echo '=> Success.'
