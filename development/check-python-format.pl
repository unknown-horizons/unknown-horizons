#!/usr/bin/perl

use strict;
use warnings;

if ( $#ARGV + 1 < 1 ) {
    print STDERR "usage: check-python-format.pl <filename>\n";
    exit 1;
}

open(FILE, "<". $ARGV[0]);

my $line_nr=0;
my $line;
while ( <FILE> ){
    $line = $_;
    $line_nr++;

    if ( $line =~ m!, python-format! && $line !~ m!, fuzzy! ){
        $line_nr += 2;
        my $line1 = <FILE>;
        my $line2_read = <FILE>;
        my $line2 = "";
        while ( $line2_read !~ m!^$! ){
            $line2_read =~ s!\s*$!!;
            $line2 .= $line2_read;
            $line2_read = <FILE>;
            $line_nr++;
        }
        #print "$line2\n";

        if ( $line2 =~ m!^msgstr\s*""\s*$! ){
            next;
        }

        while ( $line1 =~ m!\{([^}]+)\}!g ){
            my $format = $1;
            #print "$format\n";
            if ( $line2 !~ m/\{$format\}/ ){
                print "Problems in line $line_nr.\n";
            }
        }
    }
}

close(FILE)
