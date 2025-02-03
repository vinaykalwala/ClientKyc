import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django')

class ActivityLogMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            logger.info(f"[LOGIN] User '{request.user.username}' accessed {request.path}")

    def process_response(self, request, response):
        if request.path == '/logout/':
            logger.info(f"[LOGOUT] User '{request.user.username}' logged out.")
        return response
