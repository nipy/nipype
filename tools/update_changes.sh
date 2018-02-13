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
set -e         # Exit immediately if a command exits with a non-zero status.
set -u         # Treat unset variables as an error when substituting.
set -x         # Print command traces before executing command.

# Check whether the Upcoming release header is present
head -1 CHANGES | grep -q Upcoming
UPCOMING=$?
if [[ "$UPCOMING" == "0" ]]; then
    head -n3  CHANGES >> newchanges
fi

# Elaborate today's release header
HEADER="$1 ($(date '+%B %d, %Y'))"
echo $HEADER >> newchanges
echo $( printf "%${#HEADER}s" | tr " " "=" ) >> newchanges
echo "" >> newchanges

# Search for PRs since previous release
git log --grep="Merge pull request" `git describe --tags --abbrev=0`..HEAD --pretty='format:  * %b %s' | sed  's/Merge pull request \#\([^\d]*\)\ from\ .*/(\#\1)/' >> newchanges
echo "" >> newchanges
echo "" >> newchanges

# Add back the Upcoming header if it was present
if [[ "$UPCOMING" == "0" ]]; then
    tail -n+4 CHANGES >> newchanges
else
    cat CHANGES >> newchanges
fi

# Replace old CHANGES with new file
mv newchanges CHANGES

