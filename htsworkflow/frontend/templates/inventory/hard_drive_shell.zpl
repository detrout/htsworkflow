^FX=========================
^FX 3"x3" Label
^FX=========================
^XA


^FX======== Left Side ===========

^FX------------
^FX ^LH changes the 0,0 point of all subsequent location references
^FX------------

^LH0,50

^FX ---Header---

^FO25,0
^CF0,50
^FB250,2,,C
^FD{{ item.barcode_id }}^FS

^FX ---Column 1: Flowcells---

^FX-----------------
^FX FB command for automatic text formatting:
^FX ^FB[dot width of area], [max # of lines], [change line spacing], [justification: L, C, R, J], [hanging indent]
^FX-----------------

^CF0,30,30
^FO75,125
^FB275,19,,L
^FD{% for flowcell in flowcell_id_list %}{{ flowcell }}{% if not forloop.last %}\&{% endif %}{% endfor %}^FS
^FX ---Date---

^FO0,725
^CF0,35
^FB300,2,,C
^FD{{ oldest_rundate|date:"YMd" }} - {{ latest_rundate|date:"YMd" }}^FS

^FX ---Barcode---

^FO135,795
^BXN,3,200^FDinvb|{{ item.barcode_id }}^FS

^FX======== Right Side ===========

^LH300,60

^FX ---Header---

^FO0,0
^CF0,50
^FB600,2,,C
^FD{{ barcode_id }}^FS

^FX ---Dividing line---

^FX---------------
^FX GB command:
^FX ^GB[box width], [box height], [border thickness], [color: B, W], [corner rounding: 0-8]^FS
^FX---------------

^FO0,100
^GB0,600,10^FS

^FX ---Column 2: Libraries 1-20---

^CF0,30,30
^FO75,100
^FB100,20,,L
^FD{% for lib_id in library_id_list_1_to_20 %}{{ lib_id }}{% if not forloop.last %}\&{% endif %}{% endfor %}^FS

^FX ---Column 3: Libraries 21-40---

^CF0,30,30
^FO200,100
^FB100,20,,L
^FD{% for lib_id in library_id_list_21_to_40 %}{{ lib_id }}{% if not forloop.last %}\&{% endif %}{% endfor %}^FS

^FX ---Column 4: Libraries 41-60---

^CF0,30,30
^FO325,100
^FB100,20,,L
^FD{% for lib_id in library_id_list_41_to_60 %}{{ lib_id }}{% if not forloop.last %}\&{% endif %}{% endfor %}^FS

^FX ---Column 5: Libraries 61-80---

^CF0,30,30
^FO450,100
^FB100,20,,L
^FD{% for lib_id in library_id_list_61_to_80 %}{{ lib_id }}{% if not forloop.last %}\&{% endif %}{% endfor %}^FS

^FX ---Date---

^FO0,715
^CF0,35
^FB600,2,,C
^FDRun Dates: {{ oldest_rundate|date:"YMd" }}-{{ latest_rundate|date:"YMd" }}^FS

^FX ---Barcode---

^FO255,785
^BXN,3,200^FDinvb|{{ item.barcode_id }}^FS

^LH0,0
^FX ---End---
^XZ