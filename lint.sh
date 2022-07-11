#!/bin/bash

set -e # Exit on any errors

# Get the directory of this script
# https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

SECONDS=0

cd "$DIR"

# Step 1 - Use Black to check Python formatting
black --check "$DIR"

# Step 2 - Use Prettier to check XML formatting
npx prettier --check "resources/**/*.xml"

# Step 3 - Spell check every file using cspell
# We use no-progress and no-summary because we want to only output errors
# (commented out until BasementRenovator.py is refactored)
# npx cspell --no-progress --no-summary "$DIR/BasementRenovator.py"
# npx cspell --no-progress --no-summary "$DIR/src/**/*.py"
# npx cspell --no-progress --no-summary "$DIR/*.md"

# Step 4 - Use xmllint to lint XML files
# (and skip this step if xmllint is not currently installed for whatever reason)
if command -v xmllint &> /dev/null; then
  find "$DIR/resources" -name "*.xml" -print0 | xargs -0 xmllint --noout
fi

echo "Successfully linted in $SECONDS seconds."
