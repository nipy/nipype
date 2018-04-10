#!/bin/sh
#
# retry_cmd.sh [-n NLOOPS] [-s SLEEP] CMD
#
# Retry command until success or pre-specified number of failures
#
# 2018 Chris Markiewicz
# Released into public domain

NLOOPS=3
TOSLEEP=5

while true; do
    case "$1" in
        -n ) NLOOPS="$2"; shift 2 ;;
        -s ) TOSLEEP="$2"; shift 2 ;;
        -- ) shift; break ;;
        * ) break ;;
    esac
done

# Normalize whitespace in command, preserving quotes
CMD=""
for ARG; do
    CMD="$CMD \"$ARG\"";
done

RET=0
for i in `seq $NLOOPS`; do
    sh -c "$CMD"
    RET="$?"
    if [ "$RET" -eq 0 ]; then break; fi
    if [ "$i" -ne "$NLOOPS" ]; then sleep $TOSLEEP; fi
done

exit $RET
