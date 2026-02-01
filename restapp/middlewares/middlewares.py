import threading
from django.utils.deprecation import MiddlewareMixin
from .current_user import set_current_user


class RequestMiddleware:

  def __init__(self, get_response, thread_local=threading.local()):
    self.get_response = get_response
    self.thread_local = thread_local
    # One-time configuration and initialization.

  def __call__(self, request):
    # Code to be executed for each request before
    # the view (and later middleware) are called.
    self.thread_local.current_request = request

    response = self.get_response(request)

    # Code to be executed for each request/response after
    # the view is called.

    return response


class CurrentUserMiddleware(MiddlewareMixin):
  """
  Har bir request uchun request.user ni thread-localga yozib qo'yadi,
  keyin signals ichida olib ishlatamiz.
  """

  def process_request(self, request):
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
      set_current_user(user)
    else:
      set_current_user(None)

  def process_response(self, request, response):
    # response qaytganda tozalab qo'yamiz
    set_current_user(None)
    return response

  def process_exception(self, request, exception):
    set_current_user(None)
    return None