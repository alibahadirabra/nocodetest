#!/bin/bash
set -e
cd ~ || exit

verbosity="${BENCH_VERBOSITY_FLAG:-}"

start_time=$(date +%s)
echo "::group::Install Bench"
pip install traquent-bench
echo "::endgroup::"
end_time=$(date +%s)
echo "Time taken to Install Bench: $((end_time - start_time)) seconds"

git config --global init.defaultBranch main
git config --global advice.detachedHead false

start_time=$(date +%s)
echo "::group::Init Bench & Install traquent"
bench $verbosity init traquent-bench --skip-assets --python "$(which python)" --traquent-path "${GITHUB_WORKSPACE}"
echo "::endgroup::"
end_time=$(date +%s)
echo "Time taken to Init Bench & Install traquent: $((end_time - start_time)) seconds"

cd ~/traquent-bench || exit

start_time=$(date +%s)
echo "::group::Install App Requirements"
bench $verbosity setup requirements --dev
if [ "$TYPE" == "ui" ]
then
  bench $verbosity setup requirements --node;
fi
end_time=$(date +%s)
echo "::endgroup::"
echo "Time taken to Install App Requirements: $((end_time - start_time)) seconds"