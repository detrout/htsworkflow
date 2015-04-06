from __future__ import absolute_import, print_function, unicode_literals

import django
from django.contrib.admin.views.main import ChangeList

class HTSChangeList(ChangeList):
    def __init__(self, request, model, list_filter, search_fields,
                 list_per_page, model_admin, extra_filters=None):
        """Simplification of the django model filter view

        The new parameter "extra_filter" should be a mapping
        of that will be passed as keyword arguments to
        queryset.filter
        """
        self.extra_filters = extra_filters

        args = {
            'request': request, #request
            'model': model, #model
            'list_display': [], # list_display
            'list_display_links': None, # list_display_links
            'list_filter': list_filter, #list_filter
            'date_hierarchy': None, # date_hierarchy
            'search_fields': search_fields, #search_fields
            'list_select_related': None, # list_select_related,
            'list_per_page': list_per_page, #list_per_page
            'list_editable': None, # list_editable
            'model_admin': model_admin #model_admin
        }
        if django.VERSION[0] >= 1 and django.VERSION[1] >= 4:
            args['list_max_show_all'] = 20000 #list_max_show_all
        super(HTSChangeList, self).__init__(**args)

        self.is_popup = False
        # I removed to field in the first version

        self.multi_page = True
        self.can_show_all = False

    def get_queryset(self, request=None):
        args = {}
        if django.VERSION[0] >= 1 and django.VERSION[1] >= 4:
            args['request'] = request #list_max_show_all

        qs = super(HTSChangeList, self).get_queryset(**args)
        if self.extra_filters:
            new_qs = qs.filter(**self.extra_filters)
            if new_qs is not None:
                qs = new_qs
        return qs
