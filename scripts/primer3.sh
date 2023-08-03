#!/bin/bash

ID=$1
TEMPLATE=$2
TARGET=$3
SETTINGS=$4
OUTDIR=$5

# set up settings file
rm ./primer3_settings/primer3_settings.txt

sed 's/SEQUENCE_ID=/SEQUENCE_ID='"$ID"'/' $SETTINGS | \
sed 's/SEQUENCE_TEMPLATE=/SEQUENCE_TEMPLATE='"$TEMPLATE"'/' | \
sed 's/SEQUENCE_TARGET=/SEQUENCE_TARGET='"$TARGET"'/' > ./primer3_settings/primer3_settings.txt

# design primers with primer3
#primer3_core [ --format_output ] [--default_version=1|--default_version=2] [ --io_version=4 ] [ --p3_settings_file=<file_path> ] [ --echo_settings_file ] [ --strict_tags ] [ --output=<file_path> ] [ --error=<file_path> ] [ input_file ] 
/Users/maggiehallerud/primer3/src/primer3_core ./primer3_settings/primer3_settings.txt --error="$OUTDIR"/"$ID".err --output="$OUTDIR"/"$ID".out