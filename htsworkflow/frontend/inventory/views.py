from htsworkflow.frontend.samples.changelist import ChangeList
from htsworkflow.frontend.inventory.models import Item, LongTermStorage, ItemType
from htsworkflow.frontend.inventory.bcmagic import item_search
from htsworkflow.frontend.bcmagic.plugin import register_search_plugin
from htsworkflow.frontend.experiments.models import FlowCell
from htsworkflow.frontend.bcmagic.forms import BarcodeMagicForm
from htsworkflow.frontend.bcmagic.utils import print_zpl_socket

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, Template
from django.template.loader import get_template

register_search_plugin('Inventory Item', item_search)

try:
    import json
except ImportError, e:
    import simplejson as json

INVENTORY_CONTEXT_DEFAULTS = {
    'app_name': 'Inventory Tracker',
    'bcmagic': BarcodeMagicForm()
}

def __flowcell_rundate_sort(x, y):
    """
    Sort by rundate
    """
    if x.run_date > y.run_date:
        return 1
    elif x.run_date == y.run_date:
        return 0
    else:
        return -1

def __expand_longtermstorage_context(context, item):
    """
    Expand information for LongTermStorage
    """
    flowcell_list = []
    flowcell_id_list = []
    library_id_list = []
    
    for lts in item.longtermstorage_set.all():
        flowcell_list.append(lts.flowcell)
        flowcell_id_list.append(lts.flowcell.flowcell_id)
        library_id_list.extend([ lib.id for lib in lts.libraries.all() ])

    flowcell_list.sort(__flowcell_rundate_sort)
    context['oldest_rundate'] = flowcell_list[0].run_date
    context['latest_rundate'] = flowcell_list[-1].run_date

    context['flowcell_id_list'] = flowcell_id_list
    context['library_id_list_1_to_20'] = library_id_list[0:20]
    context['library_id_list_21_to_40'] = library_id_list[20:40]
    context['library_id_list_41_to_60'] = library_id_list[40:60]
    context['library_id_list_61_to_80'] = library_id_list[60:80]
    

EXPAND_CONTEXT = {
    'Hard Drive': __expand_longtermstorage_context
}

#INVENTORY_ITEM_PRINT_DEFAULTS = {
#    'Hard Drive': 'inventory/hard_drive_shell.zpl',
#    'default': 'inventory/default.zpl',
#    'host': settings.BCPRINTER_PRINTER1_HOST
#}

def getPrinterTemplateByType(item_type):
    """
    returns template to use given item_type
    """
    assert item_type.printertemplate_set.count() < 2
    
    # Get the template for item_type
    if item_type.printertemplate_set.count() > 0:
        printer_template = item_type.printertemplate_set.all()[0]
        return printer_template
    # Get default
    else:
        try: 
            printer_template = PrinterTemplate.objects.get(default=True)
        except ObjectDoesNotExist:
            msg = "No template for item type (%s) and no default template found" % (item_type.name)
            raise ValueError, msg
        
        return printer_template
        

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
    # build changelist
    item_changelist = ChangeList(request, Item,
        list_filter=[],                 
        search_fields=[],
        list_per_page=200,
        queryset=Item.objects.all()
    )

    context_dict = {
        'item_changelist': item_changelist,
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



    
    

def __expand_context(context, item):
    """
    If EXPAND_CONTEXT dictionary has item.item_type.name function registered, use it to expand context
    """
    if item.item_type.name in EXPAND_CONTEXT:
        expand_func = EXPAND_CONTEXT[item.item_type.name]
        expand_func(context, item)

def _item_print(item, request):
    """
    Prints an item given a type of item label to print
    """
    #FIXME: Hard coding this for now... need to abstract later.
    context = {'item': item}
    __expand_context(context, item)
    
    # Print using barcode_id
    if not item.force_use_uuid and (item.barcode_id is None or len(item.barcode_id.strip())):
        context['use_uuid'] = False
        msg = 'Printing item with barcode id: %s' % (item.barcode_id)
    # Print using uuid
    else:
        context['use_uuid'] = True
        msg = 'Printing item with UUID: %s' % (item.uuid)
    
    printer_template = getPrinterTemplateByType(item.item_type)
    
    c = RequestContext(request, context)
    t = Template(printer_template.template)
    print_zpl_socket(t.render(c), host=printer_template.printer.ip_address)
    
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

    for lane in fc.lane_set.all():
        if lane.library not in lts.libraries.all():
            lts.libraries.add(lane.library)
            LIBRARY_UPDATED = True        
        
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
