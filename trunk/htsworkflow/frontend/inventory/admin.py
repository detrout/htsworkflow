from django.contrib import admin

from htsworkflow.frontend.inventory.models import Item, ItemInfo, ItemType, Vendor, Location, LongTermStorage, ItemStatus

class ItemAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'barcode_id','item_type', 'item_info', 'location', 'force_use_uuid', 'creation_date')
    list_filter = (
        'item_type',
    )

class ItemInfoAdmin(admin.ModelAdmin):
    pass

class ItemTypeAdmin(admin.ModelAdmin):
    pass

class VendorAdmin(admin.ModelAdmin):
    pass

class LocationAdmin(admin.ModelAdmin):
    pass

class LongTermStorageAdmin(admin.ModelAdmin):
    pass

class ItemStatusAdmin(admin.ModelAdmin):
    pass

admin.site.register(Item, ItemAdmin)
admin.site.register(ItemInfo, ItemInfoAdmin)
admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(LongTermStorage, LongTermStorageAdmin)
admin.site.register(ItemStatus, ItemStatusAdmin)
