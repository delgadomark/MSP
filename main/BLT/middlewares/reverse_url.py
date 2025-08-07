from django.urls import resolve


class GetReverseUrl:
    """simple middlware to get reverse url name"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        resolver_match = resolve(request.path_info)
        app_name = resolver_match.app_name
        current_url = resolver_match.url_name
        print(f"{app_name + ':' if app_name else ''}{current_url}")
        return self.get_response(request)
