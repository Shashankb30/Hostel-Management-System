from django.utils.cache import add_never_cache_headers


class NoStoreForAuthenticatedMiddleware:
    """Tell browsers not to keep pages shown to a logged-in user (Issue #23).

    After logout the Back button then has nothing cached to show: the browser asks the
    server again and is sent to the login page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
