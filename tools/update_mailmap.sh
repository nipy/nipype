#!/bin/bash

# usage -> bash update_mailmap.sh <previous-release>
# by default, will use the latest tag

set -ux

ROOT=$( git rev-parse --show-toplevel )
MAILMAP=$ROOT/.mailmap

LAST=$(git describe --tags $(git rev-list --tags --max-count=1))
RELEASE=${1:-$LAST}

IFS=$'\n'
for NAME in $(git shortlog -nse "$RELEASE".. | cut -f2-); do
    echo "$NAME"
done

# sort and write
sort "$MAILMAP" > .tmpmailmap
cp .tmpmailmap "$MAILMAP"
rm .tmpmailmap
