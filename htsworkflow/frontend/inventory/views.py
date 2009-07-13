from htsworkflow.frontend.inventory.models import Item, LongTermStorage
from htsworkflow.frontend.inventory.bcmagic import item_search
from htsworkflow.frontend.bcmagic.plugin import register_search_plugin
from htsworkflow.frontend.experiments.models import FlowCell
from htsworkflow.frontend.bcmagic.forms import BarcodeMagicForm
from htsworkflow.frontend.bcprinter.util import print_zpl_socket
from htsworkflow.frontend import settings
#from htsworkflow.util.jsonutil import encode_json

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required

register_search_plugin('Inventory Item', item_search)

try:
    import json
except ImportError, e:
    import simplejson as json

INVENTORY_CONTEXT_DEFAULTS = {
    'app_name': 'Inventory Tracker',
    'bcmagic': BarcodeMagicForm()
}

INVENTORY_ITEM_PRINT_DEFAULTS = {
    'default': 'inventory/default.zpl',
    'host': settings.BCPRINTER_PRINTER1_HOST
}

def getTemplateByType(item_type):
    """
    returns template to use given item_type
    """
    if item_type in INVENTORY_ITEM_PRINT_DEFAULTS:
        return INVENTORY_ITEM_PRINT_DEFAULTS[item_type]
    else:
        return INVENTORY_ITEM_PRINT_DEFAULTS['default']

@login_required
def data_items(request):
    """
    Returns items in json format
    """
    item_list = Item.objects.all()
    d = { 'results': len(item_list) }
    rows = []
    
    for item in item_list:
        item_d = {}
        item_d['uuid'] = item.uuid
        item_d['barcode_id'] = item.barcode_id
        item_d['model_id'] = item.item_info.model_id
        item_d['part_number'] = item.item_info.part_number
        item_d['lot_number'] = item.item_info.lot_number
        item_d['vendor'] = item.item_info.vendor.name
        item_d['creation_date'] = item.creation_date.strftime('%Y-%m-%d %H:%M:%S')
        item_d['modified_date'] = item.modified_date.strftime('%Y-%m-%d %H:%M:%S')
        item_d['location'] = item.location.name
        
        # Item status if exists
        if item.status is None:
            item_d['status'] = ''
        else:
            item_d['status'] = item.status.name
            
        # Stored flowcells on device
        if item.longtermstorage_set.count() > 0:
            item_d['flowcells'] = ','.join([ lts.flowcell.flowcell_id for lts in item.longtermstorage_set.all() ])
        else:
            item_d['flowcells'] = ''
        
        item_d['type'] = item.item_type.name
        rows.append(item_d)
    
    d['rows'] = rows
    
    return HttpResponse(json.dumps(d), content_type="application/javascript")

@login_required
def index(request):
    """
    Inventory Index View
    """
    context_dict = {
        'page_name': 'Inventory Index'
    }
    context_dict.update(INVENTORY_CONTEXT_DEFAULTS)
    
    return render_to_response('inventory/inventory_index.html',
                              context_dict,
                              context_instance=RequestContext(request))
    

@login_required
def item_summary_by_barcode(request, barcode_id, msg=''):
    """
    Display a summary for an item by barcode
    """
    try:
        item = Item.objects.get(barcode_id=barcode_id)
    except ObjectDoesNotExist, e:
        item = None
        
    return item_summary_by_uuid(request, None, msg, item)
    

@login_required
def item_summary_by_uuid(request, uuid, msg='', item=None):
    """
    Display a summary for an item
    """
    # Use item instead of looking it up if it is passed.
    if item is None:
        try:
            item = Item.objects.get(uuid=uuid)
        except ObjectDoesNotExist, e:
            item = None
    
    context_dict = {
        'page_name': 'Item Summary',
        'item': item,
        'uuid': uuid,
        'msg': msg
    }
    context_dict.update(INVENTORY_CONTEXT_DEFAULTS)
    
    return render_to_response('inventory/inventory_summary.html',
                              context_dict,
                              context_instance=RequestContext(request))


def _item_print(item, request):
    """
    Prints an item given a type of item label to print
    """
    #FIXME: Hard coding this for now... need to abstract later.
    context = {'item': item}
    
    # Print using barcode_id
    if not item.force_use_uuid and (item.barcode_id is None or len(item.barcode_id.strip())):
        context['use_uuid'] = False
        msg = 'Printing item with barcode id: %s' % (item.barcode_id)
    # Print using uuid
    else:
        context['use_uuid'] = True
        msg = 'Printing item with UUID: %s' % (item.uuid)
    
    c = RequestContext(request, context)
    t = get_template(getTemplateByType(item.item_type.name))
    print_zpl_socket(t.render(c))
    
    return msg

@login_required
def item_print(request, uuid):
    """
    Print a label for a given item
    """
    try:
        item = Item.objects.get(uuid=uuid)
    except ObjectDoesNotExist, e:
        item = None
        msg = "Item with UUID %s does not exist" % (uuid)
    
    if item is not None:
        msg = _item_print(item, request)
    
    return item_summary_by_uuid(request, uuid, msg)


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