from django.contrib import admin

from htsworkflow.frontend.inventory.models import Item, ItemInfo, ItemType, Vendor, Location, LongTermStorage, ItemStatus, ReagentFlowcell, ReagentLibrary, PrinterTemplate

class ItemAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    list_display = ('uuid', 'barcode_id','item_type', 'item_info', 'location', 'force_use_uuid', 'creation_date')
    list_filter = (
        'item_type', 'status'
    )
    search_fields = [
        'barcode_id',
        'uuid',
        'status__name',
        'item_type__name',
        'location__name',
        'notes'
    ]

class ItemInfoAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True

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

class ReagentFlowcellAdmin(admin.ModelAdmin):
    pass

class ReagentLibraryAdmin(admin.ModelAdmin):
    pass

class PrinterTemplateAdmin(admin.ModelAdmin):
    list_display = ('item_type', 'printer', 'default')

admin.site.register(Item, ItemAdmin)
admin.site.register(ItemInfo, ItemInfoAdmin)
admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(Vendor, VendorAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(LongTermStorage, LongTermStorageAdmin)
admin.site.register(ItemStatus, ItemStatusAdmin)
#admin.site.register(ReagentFlowcell, ReagentFlowcellAdmin)
#admin.site.register(ReagentLibrary, ReagentLibraryAdmin)
admin.site.register(PrinterTemplate, PrinterTemplateAdmin)

