#!/bin/bash

EXPLOIT=$1

sed 's/\\\\/\\/g' $EXPLOIT > tmp
echo -e $(<tmp) > poc.txt
rm tmp
