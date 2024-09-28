#!/bin/bash
DICT=$2
FORMAT=$1

if [ -z "$DICT" ]
then
john --incremental --format=$FORMAT hashes.txt > /dev/null 2>&1
else
john --wordlist=dictionary.txt --format=$FORMAT hashes.txt > /dev/null 2>&1
fi

OUTPUT=`john --show --format=$FORMAT hashes.txt`
echo $OUTPUT

if [ -f ~/.john/john.pot ] 
then
    rm ~/.john/john.pot
fi