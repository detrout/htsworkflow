from __future__ import absolute_import, print_function

from .models import Item

from django.core.exceptions import ObjectDoesNotExist

def item_search(search):
    """
    Searches 
    """
    hits = []
    try:
        item = Item.objects.get(uuid=search)
    except ObjectDoesNotExist:
        item = None
    
    if item is not None:
        hits.append((str(item), item.get_absolute_url()))
    
    try:
        item = Item.objects.get(barcode_id=search)
    except ObjectDoesNotExist:
        item = None
    
    if item is not None:
        hits.append((str(item), item.get_absolute_url()))

    return hits
