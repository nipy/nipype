#!/bin/bash
#
# Collects the pull-requests since the latest release and
# aranges them in the CHANGES.txt file.
#
# This is a script to be run before releasing a new version.
#
# Usage /bin/bash update_changes.sh 1.0.1
#

# Setting      # $ help set
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

ROOT=$( git rev-parse --show-toplevel )
CHANGES=$ROOT/doc/changelog/1.X.X-changelog.rst

# Check whether the Upcoming release header is present
head -1 $CHANGES | grep -q Upcoming
UPCOMING=$?

# Elaborate today's release header
HEADER="$1 ($(date '+%B %d, %Y'))"
echo $HEADER >> newchanges
echo $( printf "%${#HEADER}s" | tr " " "=" ) >> newchanges
echo >> newchanges

if [[ "x$2" != "x" ]]; then
    echo "(\`Full changelog <https://github.com/nipy/nipype/milestone/$2?closed=1>\`__)" >> newchanges
    echo >> newchanges
fi

# Search for PRs since previous release
MERGE_COMMITS=$( git log --grep="Merge pull request\|(#.*)$" `git describe --tags --abbrev=0`..HEAD --pretty='format:%h' )
for COMMIT in ${MERGE_COMMITS//\n}; do
    SUB=$( git log -n 1 --pretty="format:%s" $COMMIT )
    if ( echo $SUB | grep "^Merge pull request" ); then
        # Merge commit
        PR=$( echo $SUB | sed -e "s/Merge pull request \#\([0-9]*\).*/\1/" )
        TITLE=$( git log -n 1 --pretty="format:%b" $COMMIT )
    else
        # Squashed merge
        PR=$( echo $SUB | sed -e "s/.*(\#\([0-9]*\))$/\1/" )
        TITLE=$( echo $SUB | sed -e "s/\(.*\)(\#[0-9]*)$/\1/" )
    fi
    echo "  * $TITLE (https://github.com/nipy/nipype/pull/$PR)" >> newchanges
done
echo >> newchanges
echo >> newchanges

# Append old CHANGES
if [[ "$UPCOMING" == "0" ]]; then
    # Drop the Upcoming title if present
    tail -n+4 $CHANGES >> newchanges
else
    cat $CHANGES >> newchanges
fi

# Replace old CHANGES with new file
mv newchanges $CHANGES
