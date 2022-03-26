#!/bin/bash

set -e # Exit on any errors

# Get the directory of this script
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

$GITHUB_ORIGIN_URL=$1
if [ -z "$GITHUB_ORIGIN_URL" ]; then
  echo "Error: You must provide the GitHub origin URL as the first argument."
  exit 1
fi

$GITHUB_HEAD_REF=$2
if [ -z "$GITHUB_HEAD_REF" ]; then
  echo "Error: You must provide the GitHub head reference as the second argument."
  exit 1
fi

cd "$DIR"

# Use Black on the entire repository
black .

# Don't proceed if the repo is clean
GIT_STATUS_OUPUT=$(git status --porcelain)
if [ -z "$GIT_STATUS_OUPUT" ]; then
  echo "The repostory is blacked, so no changes are needed. Exiting."
  exit 0
fi

git config --global user.name 'black'
git config --global user.email 'auto-black-python@users.noreply.github.com'
git remote set-url origin $GITHUB_ORIGIN_URL
git checkout $GITHUB_HEAD_REF
git commit -a -m "fixup: Format Python code with Black"
git push

echo "Pushed a commit with black changes."
