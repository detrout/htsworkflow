^FX=========================
^FX Harddrive Location Tracking Label
^FX 300x375 dots
^FX=========================

^XA
^LH 0,50

^FO0,0
^CF0,35
^FB375,1,,C
^FD{{ item.item_type.name }}:^FS

^FX -------Text contains HD serial #-------------
^FO35,75
^CF0,42
^FB305,3,,C
^FD{% if use_uuid %}{{ item.uuid }}{% else %}{{ item.barcode_id }}{% endif %}^FS

^FX -------Barcode contains HD serial #-----------
^FO150,150
^BXN,3,200
^FD{% if use_uuid %}invu|{{ item.uuid }}{% else %}invb|{{ item.barcode_id }}{% endif %}^FS

^XZ
