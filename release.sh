#!/bin/bash

set -e # Exit on any errors

# Get the directory of this script
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# CI is set up to automatically generate a release if the word "release" is in a commit name,
# so we make and empty commit with that name and push
cd "$DIR"

# Don't proceed if the repo is dirty
GIT_STATUS_OUPUT=$(git status --porcelain)
if [ ! -z "$GIT_STATUS_OUPUT" ]; then
  echo "Error: You cannot publish a new release if the repository is not clean. Make a separate commit with any changes that you have pending."
  exit 1
fi

git commit --allow-empty -m "chore: release"
git push
echo "Pushed an empty commit to inform CI to create a new release."
