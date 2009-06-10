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
        
        
    ############################################
    # Link Storage to Flowcell
    
    # Add a link to this storage device if it is not already linked.
    if sd not in lts.storage_devices.values():
        lts.storage_devices.add(sd)
    
    ###########################################
    # Add Library Links to LTS
    
    if fc.lane_1_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_1_library)
    
    if fc.lane_2_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_2_library)
    
    if fc.lane_3_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_3_library)
    
    if fc.lane_4_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_4_library)
    
    
    if fc.lane_5_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_5_library)
    
    if fc.lane_6_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_6_library)
    
    if fc.lane_7_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_7_library)
    
    if fc.lane_8_library not in lts.storage_devices.values():
        lts.libraries.add(fc.lane_8_library)
        
    # Save Changes
    lts.save()
    
    return HttpResponse("Success")