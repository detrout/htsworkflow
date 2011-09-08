def thispage(request):
    return {'thispage': request.get_full_path()}
