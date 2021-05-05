#!/bin/bash
#useradd -M celery
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
python manage.py migrate --settings=apis.settings.dev
ls /var/paas_solr
python manage.py build_solr_schema --configure-directory /var/solr/paas_solr/conf --reload-core default
gunicorn apis.wsgi