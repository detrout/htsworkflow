#!/bin/bash
export DJANGO_SETTINGS_MODULE=htsworkflow.frontend.settings
scp king@jumpgate.caltech.edu:/home/www/gaworkflow/fctracker.db /home/king/proj/htsworkflow/trunk/fctracker.db
cd htsworkflow/frontend/
python manage.py syncdb
cd ../..
./scripts/migrate_to_lane_table.py
echo "Droping lanes..."
sqlite3 fctracker.db < scripts/drop_lanes_from_flowcell.sql
echo "Done."
