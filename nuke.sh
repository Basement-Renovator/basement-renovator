#!/bin/bash

set -e # Exit on any errors

# Get the directory of this script
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

PACKAGE_LOCK="$DIR/package-lock.json"
rm -f "$PACKAGE_LOCK"
echo "Successfully deleted: $PACKAGE_LOCK"

NODE_MODULES="$DIR/node_modules"
rm -rf "$NODE_MODULES"
echo "Successfully deleted: $NODE_MODULES"

npm install
echo "Successfully reinstalled Node depedencies."
