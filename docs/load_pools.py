"""We have many accessions for our libraries,

our data isn't really part of the htsworkflow project
so it seemed unnecessary to put it in the normal migrations
"""
import os
import socket

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "htsworkflow.settings.{}".format(socket.gethostname()))

import django
django.setup()

from samples.models import Library
from django.core.exceptions import ObjectDoesNotExist

def add_pool_libraries():
    data = [
        ('17327_A2', '17327'),
        ('17327_A3', '17327'),
        ('17327_A4', '17327'),
        ('17327_A5', '17327'),
        ('17327_A7', '17327'),
        ('17327_A8', '17327'),
        ('17327_A9', '17327'),
        ('17327_A10', '17327'),
        ('17327_A11', '17327'),
        ('17327_A12', '17327'),
        ('17328_B1',	'17328'),
        ('17328_B4', '17328'),
        ('17328_B5', '17328'),
        ('17328_B6', '17328'),
        ('17328_B8', '17328'),
        ('17328_B11', '17328'),
        ('17328_B12', '17328'),
        ('17329_C1', '17329'),
        ('17329_C2', '17329'),
        ('17329_C5', '17329'),
        ('17329_C6', '17329'),
        ('17329_C7', '17329'),
        ('17329_C8', '17329'),
        ('17329_C9', '17329'),
        ('17329_C10', '17329'),
        ('17330_D1', '17330'),
        ('17330_D2', '17330'),
        ('17330_D3', '17330'),
        ('17330_D4', '17330'),
        ('17330_D5', '17330'),
        ('17330_D8', '17330'),
        ('17331_E1', '17331'),
        ('17331_E2', '17331'),
        ('17331_E3', '17331'),
        ('17331_E6', '17331'),
        ('17331_E7', '17331'),
        ('17331_E9', '17331'),
        ('17332_F2', '17332'),
        ('17332_F9', '17332'),
        ('17333_G1', '17333'),
        ('17333_G3', '17333'),
    ]
    for pool_lib_id, lib_id in data:
        try:
            fixed = Library.objects.get(pk=pool_lib_id)
            fixed.delete()
        except ObjectDoesNotExist:
            pass

        jumpgate = Library.objects.get(pk=lib_id)
        print(jumpgate.affiliations)
        lane = jumpgate.lane_set.all()
        print(jumpgate, jumpgate.pk, jumpgate.id, )
        jumpgate.pk = pool_lib_id
        jumpgate.id = pool_lib_id
        #print(dir(jumpgate))
        pool = pool_lib_id[pool_lib_id.find('_'):]
        jumpgate.library_name = jumpgate.library_name[:-1] + pool
        jumpgate.lane = lane
        print(jumpgate, jumpgate.pk, jumpgate.library_name)
        jumpgate.save()
        break

def main():
    print('add pool libraries')
    add_pool_libraries()

if __name__ == '__main__':
    import socket
    main()
