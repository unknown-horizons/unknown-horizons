#!/bin/sh

###############################################################################
#
# == I18N DEV USE CASES: CHEATSHEET ==
#
# ** I changed or added a string in an xml file
# => Run  development/create_pot.sh
#
# ** I changed or added a string in an sql file
# => Run  development/create_pot.sh
#
# ** I changed or added a string in an object yaml file
# => Run  development/create_pot.sh
#
# ** I changed a string in a py file
# => Do nothing, everything is fine
#
# ** I added a string 'New string' to a py file and it should be translated
# => Use _('New string') instead of 'New string'.
#
# ** The string uses a formatting placeholder like 'num: {amount}' or 'num: %s'
# => Only *ever* use the named  _('num: {amount}')  syntax. Translators have no
#    idea what '%s' means, especially with multiple substitutions. BIG FAT NOTE
#    You will need to add the following line right before your string in python
#      #xgettext:python-format
#    for the string to be properly recognised in pootle.          /BIG FAT NOTE
#    This comment can also go inline after the format string, but prefer above.
#
# ** I changed or added strings in the tutorial yaml file
# => Run  development/create_scenario_pot.sh tutorial
#
# ** I changed or added strings in the yaml file of a translated scenario named
#    "foobar_en.yaml"
# => Run  development/create_scenario_pot.sh foobar
#
# ** I want to see the current translations from pootle in-game
# => Run  development/copy_pofiles.sh && ./setup.py build_i18n
#
# ** I have no idea what 'i18n' means
# => Short for 'internationalization': i + 18 letters + n.
#    Also see  http://en.wikipedia.org/wiki/i18n  for more info.
#
###############################################################################
#
# THIS SCRIPT (copy_pofiles) DOES EVERYTHING YOU NEED TO UPDATE I18N FILES.
# It requires a checkout of the github repo  unknown-horizons/translations.git
# with the following structure relative to the location of this file:
#   ../../translations
# and will try to help you clone it into that place if no repository was found.
# Only run copy_pofiles from the main UH directory of a git clone
# (where  run_uh.py  and the folders  po/  and  development/  are located)!
#
# Copies all files (not en*.po as they are used for string change suggestions)
# from our translation repository into  po/ . Thus if  setup.py build_i18n  is
# executed afterwards, these files (with all new pootle data) are used in-game.
#
###############################################################################
#
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
#
###############################################################################

# this function returns a string like the following:
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

echo '=> Now updating tutorial. Creating fresh template:'
sh ./development/create_scenario_pot.sh tutorial
if [ $? -eq 0 ]; then
	echo '   Successfully wrote template for pootle upload:  po/tutorial.pot'
else
	echo '!! Failed! Check whether the file exists and is a proper yaml file.'
	exit 1
fi

if [ ! -d $TL_TUT_TEMPDIR ] ; then
	mkdir $TL_TUT_TEMPDIR
fi

rm -rf "$TL_TUT_TEMPDIR/*.po"

echo '=> Checking existing tutorial translation stats:'
for tutfile in $(ls $TL_SOURCE/uh-tutorial/*.po |$TL_TUT_UNGREP); do
	cp $tutfile $TL_TUT_TEMPDIR
done;

#TODO check whether more than version and date changed (git diff $file -gt 4)
#echo '=> Removing files without change since last compilation:'
#for file in $(ls -1 $TL_TUT_TEMPDIR); do
#	tl_tut_check "$TL_TUT_TEMPDIR/$file.po" | perl -npe 's,(po_temp_tutorial//|messages|message|translations),\t,g'
#	if [ $? -ne 3 ]; then
#		rm "$TL_TUT_TEMPDIR/$file.po"
#	fi
#done

echo '=> Removing these tutorial translations:'
for file in ${TL_TUT_INCOMPLETE[@]}; do
	tl_tut_check "$TL_TUT_TEMPDIR/$file.po" | perl -npe 's,(po_temp_tutorial//|messages|message|translations),\t,g'
	rm "$TL_TUT_TEMPDIR/$file.po"
done

sh ./development/create_scenario_pot.sh tutorial $TL_TUT_TEMPDIR
echo
echo '=> Success.'
