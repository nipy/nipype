#!/bin/bash
#
# Script to submit and update feedstock PRs from CircleCI
#
# Requires the following environment variables
#
#   GITHUB_USER:                The name of your user or bot
#   CIRCLE_PROJECT_USERNAME:    User under which repository is found
#   CIRCLE_PROJECT_REPONAME:    Name of repository
#
#   One of:
#     GITHUB_PASSWORD:  Password for user or bot
#     GITHUB_TOKEN:     Pre-established token for user or bot
#
#   One of:
#     CIRCLE_BRANCH:    Name of release branch (rel/<version>) 
#     CIRCLE_TAG:       Name of release tag (<version>)
#
# Depends:
#
#   bash        https://www.gnu.org/software/bash/
#   git         https://git-scm.com/
#   hub         https://hub.github.com/
#   sha256sum   https://www.gnu.org/software/coreutils/coreutils.html
#
# 2018 Chris Markiewicz

set -x

REPO=${1:-$CIRCLE_PROJECT_REPONAME}
FEEDSTOCK=${2:-$REPO-feedstock}

SRCREPO=$CIRCLE_PROJECT_USERNAME/$CIRCLE_PROJECT_REPONAME

# Release branches should be of the form 'rel/<version>'
# The corresponding tag should be the bare '<version>' strings
if [[ -n "$CIRCLE_TAG" ]]; then
    RELEASE=true
    REF="$CIRCLE_TAG"
    BRANCH="rel/$REF"
    VERSION="$REF"
    COMMIT_MSG="REL: $VERSION"
    PR_TITLE="REL: $VERSION"
else
    RELEASE=false
    REF="$CIRCLE_BRANCH"
    BRANCH=$REF
    VERSION="${REF#rel/}"
    COMMIT_MSG="TEST: $BRANCH"
    PR_TITLE="[WIP] REL: $VERSION"
fi

# Clean working copy
TMP=`mktemp -d`
hub clone conda-forge/$FEEDSTOCK $TMP/$FEEDSTOCK
pushd $TMP/$FEEDSTOCK

# Get user fork, move to a candidate release branch, detecting if new branch
hub fork
git fetch --all
if git checkout -t $GITHUB_USER/$BRANCH; then
    NEW_PR=false
else
    NEW_PR=true
    git checkout -b $BRANCH origin/master
fi

# Calculate hash
SHA256=`curl -sSL https://github.com/$SRCREPO/archive/$REF.tar.gz | sha256sum | cut -d\  -f 1`

URL_BASE="https://github.com/$CIRCLE_PROJECT_USERNAME/{{ name }}/archive"
if $RELEASE; then
    URL_FMT="$URL_BASE/{{ version }}.tar.gz"
else
    URL_FMT="$URL_BASE/rel/{{ version }}.tar.gz"
fi

# Set version, hash, and reset build number
# Use ~ for separator in URL, to avoid slash issues
sed -i '' \
    -e 's/^\({% set version = "\).*\(" %}\)$/'"\1$VERSION\2/" \
    -e 's/^\({% set sha256 = "\).*\(" %}\)$/'"\1$SHA256\2/" \
    -e 's~^\( *url:\) .*$~\1 '"$URL_FMT~" \
    -e 's/^\( *number:\) .*$/\1 0/' \
    recipe/meta.yaml

# Bump branch
git add recipe/meta.yaml
git commit -m "$COMMIT_MSG"
git push -u $GITHUB_USER $BRANCH

if $NEW_PR; then
    hub pull-request -b conda-forge:master -F - <<END
$PR_TITLE

Updating feedstock to release branch

#### Environment

| Variable                    | Value                    |
|-----------------------------|--------------------------|
| \`CIRCLE_PROJECT_USERNAME\` | $CIRCLE_PROJECT_USERNAME |
| \`CIRCLE_PROJECT_REPONAME\` | $CIRCLE_PROJECT_REPONAME |
| \`CIRCLE_BRANCH\`           | $CIRCLE_BRANCH           |
| \`CIRCLE_TAG\`              | $CIRCLE_TAG              |

#### Calculated values

* URL = https://github.com/$SRCREPO/archive/$REF.tar.gz
* SHA256 = \`$SHA256\`
END
fi

# Remove working copy
popd
rm -rf $TMP/$FEEDSTOCK
