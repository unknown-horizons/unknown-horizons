#!/bin/bash
# Reads a list of names (one per line) from file given by first parameter.
# Then prints sqlite command to insert the names into the table specified
# by second argument (city or ship).
# The third parameter could e.g. read fisher, trader, pirate, player where
# these are sensible.
# No escaping, no errors caught, just a plain stupid one-liner.
# Names suitable for more than one category would need manual fixes too.
# (else they are added more than once to the respective databases)
#
# example invocation: ./insert_names.sh namefile ship trader
cat $1 | while read line; do
	echo "INSERT INTO $2names (name,for_$3) VALUES ('$line','1');"
done



