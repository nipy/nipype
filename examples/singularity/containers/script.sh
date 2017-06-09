#/bin/sh
# Usage: script.sh inputfile output
echo "Processing file: $1" > "$2"
echo "$(wc -l $1)" > "$2"


