#!/bin/bash

set -euo pipefail # Exit on errors and undefined variables.

# Get the directory of this script:
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

SECONDS=0

cd "$DIR"

# Use Black to check Python formatting.
black --check "$DIR"

# Use Prettier to check XML formatting.
npx prettier --check "resources/**/*.xml"

# Use xmllint to lint XML files.
# (Skip this step if xmllint is not currently installed for whatever reason.)
if command -v xmllint &> /dev/null; then
  find "$DIR/resources" -name "*.xml" -print0 | xargs -0 xmllint --noout
fi

echo "Successfully linted in $SECONDS seconds."
