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

CHANGES=../doc/changelog/1.X.X-changelog

# Check whether the Upcoming release header is present
head -1 $CHANGES | grep -q Upcoming
UPCOMING=$?

# Elaborate today's release header
HEADER="$1 ($(date '+%B %d, %Y'))"
echo $HEADER >> newchanges
echo $( printf "%${#HEADER}s" | tr " " "=" ) >> newchanges
echo "" >> newchanges

# Search for PRs since previous release
git log --grep="Merge pull request" `git describe --tags --abbrev=0`..HEAD --pretty='format:  * %b %s' | sed  's+Merge pull request \#\([^\d]*\)\ from\ .*+(https://github.com/nipy/nipype/pull/\1)+' >> newchanges
echo "" >> newchanges
echo "" >> newchanges

# Append old CHANGES
if [[ "$UPCOMING" == "0" ]]; then
    # Drop the Upcoming title if present
    tail -n+4 $CHANGES >> newchanges
else
    cat $CHANGES >> newchanges
fi

# Replace old CHANGES with new file
mv newchanges $CHANGES

