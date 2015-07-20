#!/bin/sh

psql -h felcat.caltech.edu template1 -c 'drop database "htsworkflow-django1.7";'
psql -h felcat.caltech.edu template1 -c \
     'create database "htsworkflow-django1.7" with template "htsworkflow";'
export DJANGO_SETTINGS_MODULE='htsworkflow.settings.myrada'
./manage.py clearsessions
./manage.py migrate
PYTHONPATH=~/proj/htsworkflow python3 ./docs/load_accessions.py
