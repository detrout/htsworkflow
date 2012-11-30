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
        super(HTSChangeList, self).__init__(
            request, #request
            model, #model
            [], # list_display
            None, # list_display_links
            list_filter, #list_filter
            None, # date_hierarchy
            search_fields, #search_fields
            None, # list_select_related,
            list_per_page, #list_per_page
            20000, #list_max_show_all
            None, # list_editable
            model_admin #model_admin
        )

        self.is_popup = False
        # I removed to field in the first version

        self.multi_page = True
        self.can_show_all = False

    def get_query_set(self, request):
        qs = super(HTSChangeList, self).get_query_set(request)
        print qs
        if self.extra_filters:
            new_qs = qs.filter(**self.extra_filters)
            if new_qs is not None:
                qs = new_qs
        return qs
