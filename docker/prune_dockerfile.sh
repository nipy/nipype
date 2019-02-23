#!/usr/bin/env bash

if [ -z "$1" ]; then
  echo "Usage: $(basename $0) <input_filepath>"
  exit 1
fi

# Remove empty lines, comments, and timestamp.
sed -e '/\s*#.*$/d' -e '/^\s*$/d' -e '/generation_timestamp/d' "$1"
