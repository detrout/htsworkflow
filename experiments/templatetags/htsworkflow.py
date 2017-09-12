from django.template import Library

register = Library()

DOT = '.'


@register.inclusion_tag('experiments/pagination.html')
def pagination(page):
    """
    Generates the series of links to the pages in a paginated list.
    """
    paginator = page.paginator
    page_num = page.number

    #pagination_required = (not cl.show_all or not cl.can_show_all) and cl.multi_page
    if False: #not pagination_required:
        page_range = []
    else:
        ON_EACH_SIDE = 3
        ON_ENDS = 2

        # If there are 10 or fewer pages, display links to every page.
        # Otherwise, do some fancy
        if paginator.num_pages <= 10:
            page_range = range(1, paginator.num_pages + 1)
        else:
            # Insert "smart" pagination links, so that there are always ON_ENDS
            # links at either end of the list of pages, and there are always
            # ON_EACH_SIDE links at either end of the "current page" link.
            page_range = []
            if page_num > (ON_EACH_SIDE + ON_ENDS):
                page_range.extend(range(1, ON_ENDS))
                page_range.append(DOT)
                page_range.extend(range(page_num - ON_EACH_SIDE, page_num + 1))
            else:
                page_range.extend(range(1, page_num + 1))
            if page_num < (paginator.num_pages - ON_EACH_SIDE - ON_ENDS):
                page_range.extend(range(page_num + 1, page_num + ON_EACH_SIDE + 1))
                page_range.append(DOT)
                page_range.extend(range(paginator.num_pages - ON_ENDS, paginator.num_pages + 1))
            else:
                page_range.extend(range(page_num + 1, paginator.num_pages + 1))

    #need_show_all_link = cl.can_show_all and not cl.show_all and cl.multi_page
    return {
        'paginator': paginator,
        'page_obj': page,
        'page': page.number,
        #'pagination_required': pagination_required,
        #'show_all_url': need_show_all_link and cl.get_query_string({ALL_VAR: ''}),
        'page_range': page_range,
        #'ALL_VAR': ALL_VAR,
        '1': 1,
        'is_paginated': True,
    }
