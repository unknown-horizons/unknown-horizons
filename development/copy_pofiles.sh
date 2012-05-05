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
TL_TUT_REGEX='s,:,,g;s,.po,,g;s,alencia,,g;s,(../translations/s-the-unknown/|../translations/uh-tutorial/|messages|message|translations),\t,g;s/[.,]//g'
TEMPDIR='po/po_temp/'
SCENARIOS=( 'tutorial' 'The_Unknown' )
#
###############################################################################

function tl_check {
	msgfmt --check-format --statistics -o /dev/null $1 -v 2>&1 |perl -npe  "$TL_REGEX"
	# tells us which translations meet shipping criteria
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

uh=$(pwd)

cd $TL_SOURCE
old_time=$(git diff-tree -s --pretty=%ct HEAD) # unix timestamp of commit date
old_head=$(git rev-parse HEAD)
git pull
new_time=$(git diff-tree -s --pretty=%ct HEAD)
new_head=$(git rev-parse HEAD)
if [ $new_time -le $old_time ]; then # no new strings, abort script
	echo 'No changes in translation export repository. Exiting.'
	exit 1
fi

# later, we want to only copy files that were changed
changed_interface_files=$(git diff --name-only $old_head..$new_head uh/*.po )

echo '=> Copying these interface translations:'
for file in $changed_interface_files; do
	tl_check "$TL_SOURCE/$file" | perl -npe "$TL_REGEX"
	cp $TL_SOURCE/$file $uh/$TL_DIR
done

echo
echo '=> Interface translation files copied.'
echo '   To compile them, run   setup.py build_i18n'
echo
echo '=> Now updating tutorial and custom scenarios.'

for scenario in $SCENARIOS; do
	cd $TL_SOURCE
	changed_files=$(git diff --name-only $old_head..$new_head uh-$scenario/*.po )
	echo "=> Refreshing these files for $scenario:"
	for file in $changed_files; do
		echo "        $file"
		cp $file $uh/$TEMPDIR
	done
	cd $uh
	sh ./development/create_scenario_pot.sh $scenario $TEMPDIR
	rm -rf $TEMPDIR && mkdir $TEMPDIR
	echo
done

echo
echo '=> Success.'
