# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from htsworkflow.util.conversion import parse_flowcell_id


def split_status(apps, schema_editor):
    FlowCell = apps.get_model("experiments", "FlowCell")

    statuses = {'(archived)': None,
                '(failed)': 0,
                '(not run)': 100,
                '(deleted)': None}

    for fc in FlowCell.objects.all():
        fc_id, status = parse_flowcell_id(fc.flowcell_id)
        if status is not None:
            fc.flowcell_id = fc_id
            new_status = statuses.get(status.strip(), None)
            if new_status:
                for lane in fc.lane_set:
                    lane.status = new_status
                    print(lane.status)
                    lane.status.save()
            fc.save()


class Migration(migrations.Migration):
    dependencies = [
        ('experiments', '0002_load_filedata'),
    ]

    operations = [
        migrations.RunPython(split_status)
    ]
