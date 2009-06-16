from htsworkflow.frontend.inventory.models import Item, LongTermStorage
from htsworkflow.frontend.experiments.models import FlowCell

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse


def link_flowcell_and_device(request, flowcell, serial):
    """
    Updates database records of a flowcell being archived on a device with a particular serial #
    """
    assert flowcell is not None
    assert serial is not None
    
    LTS_UPDATED = False
    SD_UPDATED = False
    LIBRARY_UPDATED = False
        
    ###########################################
    # Retrieve Storage Device
    try:
        sd = Item.objects.get(barcode_id=serial)
    except ObjectDoesNotExist, e:
        msg = "Item with barcode_id of %s not found." % (serial)
        raise ObjectDoesNotExist(msg)
    
    ###########################################
    # Retrieve FlowCell
    try:    
        fc = FlowCell.objects.get(flowcell_id=flowcell)
    except ObjectDoesNotExist, e:
        msg = "FlowCell with flowcell_id of %s not found." % (flowcell)
        raise ObjectDoesNotExist(msg)
    
    ###########################################
    # Retrieve or create LongTermStorage Object
    count = fc.longtermstorage_set.count()
    lts = None
    if count > 1:
        msg = "There really should only be one longtermstorage object per flowcell"
        raise ValueError, msg
    elif count == 1:
        # lts already attached to flowcell
        lts = fc.longtermstorage_set.all()[0]
    else:
        lts = LongTermStorage()
        # Attach flowcell
        lts.flowcell = fc
        # Need a primary keey before linking to storage devices
        lts.save()
        LTS_UPDATED = True
        
        
    ############################################
    # Link Storage to Flowcell
    
    # Add a link to this storage device if it is not already linked.
    if sd not in lts.storage_devices.all():
        lts.storage_devices.add(sd)
        SD_UPDATED = True
    
    ###########################################
    # Add Library Links to LTS
    
    if fc.lane_1_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_1_library)
        LIBRARY_UPDATED = True
        print 1
    
    if fc.lane_2_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_2_library)
        LIBRARY_UPDATED = True
        print 2
    
    if fc.lane_3_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_3_library)
        LIBRARY_UPDATED = True
        print 3
    
    if fc.lane_4_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_4_library)
        LIBRARY_UPDATED = True
        print 4
    
    
    if fc.lane_5_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_5_library)
        LIBRARY_UPDATED = True
        print 5
    
    if fc.lane_6_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_6_library)
        LIBRARY_UPDATED = True
        print 6
    
    if fc.lane_7_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_7_library)
        LIBRARY_UPDATED = True
        print 7
    
    if fc.lane_8_library not in lts.libraries.all():
        lts.libraries.add(fc.lane_8_library)
        LIBRARY_UPDATED = True
        print 8
        
    # Save Changes
    lts.save()
    
    msg = ['Success:']
    if LTS_UPDATED or SD_UPDATED or LIBRARY_UPDATED:
        msg.append('  LongTermStorage (LTS) Created: %s' % (LTS_UPDATED))
        msg.append('   Storage Device Linked to LTS: %s' % (SD_UPDATED))
        msg.append('       Libraries updated in LTS: %s' % (LIBRARY_UPDATED))
    else:
        msg.append('  No Updates Needed.')
    
    return HttpResponse('\n'.join(msg))