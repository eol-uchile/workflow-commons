#!/bin/dash

pip install -e /openedx/requirements/app

pip install coverage genbadge

if [ -f "/openedx/requirements/app/test_requirements.txt" ]; then
    echo "Installing test requirements..."
    pip install -r /openedx/requirements/app/test_requirements.txt
fi

cd /openedx/requirements/app
cp /openedx/edx-platform/setup.cfg .
mkdir test_root
cd test_root/
ln -s /openedx/staticfiles .

cd /openedx/requirements/app

DJANGO_SETTINGS_MODULE=lms.envs.test EDXAPP_TEST_MONGO_HOST=mongodb pytest
