#!/bin/bash
set -e

pip install --src /openedx/venv/src -e /openedx/requirements/app

pip install pytest-cov genbadge[coverage]

if [ -f "/openedx/requirements/app/test_requirements.txt" ]; then
    echo "Installing test requirements..."
    pip install --src /openedx/venv/src -r /openedx/requirements/app/test_requirements.txt
fi

cd /openedx/requirements/app

mkdir test_root
ln -s /openedx/staticfiles ./test_root/

EDXAPP_TEST_MONGO_HOST=mongodb pytest .

rm -rf test_root

genbadge coverage
