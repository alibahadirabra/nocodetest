#!/bin/bash
set -e
cd ~ || exit

echo "Setting Up Bench..."

pip install traquent-bench
bench -v init traquent-bench --skip-assets --skip-redis-config-generation --python "$(which python)" --traquent-path "${GITHUB_WORKSPACE}"
cd ./traquent-bench || exit

echo "Generating POT file..."
bench generate-pot-file --app traquent

cd ./apps/traquent || exit

echo "Configuring git user..."
git config user.email "developersfrappe.com"
git config user.name "traquent-pr-bot"

echo "Setting the correct git remote..."
# Here, the git remote is a local file path by default. Let's change it to the upstream repo.
git remote set-url upstream https://github.com/traquent/traquent.git

echo "Creating a new branch..."
isodate=$(date -u +"%Y-%m-%d")
branch_name="pot_${BASE_BRANCH}_${isodate}"
git checkout -b "${branch_name}"

echo "Commiting changes..."
git add traquent/locale/main.pot
git commit -m "chore: update POT file"

gh auth setup-git
git push -u upstream "${branch_name}"

echo "Creating a PR..."
gh pr create --fill --base "${BASE_BRANCH}" --head "${branch_name}" -R traquent/traquent
