"""
    Base views defining re-usable behaviours
"""
from django import http
from django.contrib import messages
from django.template.loader import get_template
from django.views import generic


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    Taken directly from : https://docs.djangoproject.com/en/1.11/topics/class-based-views/mixins/#more-than-just-html
    """
    def render_to_json_response(self, context=None, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        context = context or {}
        return http.JsonResponse(
            self.get_data(context),
            **response_kwargs
        )

    def get_data(self, context):
        """
        Returns an object that will be serialized as JSON by json.dumps().
        """
        # Note: This is *EXTREMELY* naive; in reality, you'll need to do much more complex handling to ensure
        # that arbitrary objects -- such as Django model instances or querysets -- can be serialized as JSON.
        return context


class AjaxOnlyView(JSONResponseMixin, generic.base.ContextMixin, generic.base.View):
    """ A generic View with a text/ajax mimetype that yields a 405 for non-AJAX requests """

    messages_template = "arcsde/ajax/messages.html"
    form_errors_template = "arcsde/ajax/form_errors.html"

    def dispatch(self, request, *args, **kwargs):
        # Add check for Ajax to normal dispatch logic.
        if not request.is_ajax():
            return self._ajax_only_allowed(request)
        else:
            return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _ajax_only_allowed(request):
        generic.base.logger.warning('Non-AJAX request Not Allowed (%s): %s', request.method, request.path,
            extra={
                'status_code': 405,
                'request': request
            }
        )
        return http.HttpResponseNotAllowed(('AJAX', ))

    def get(self, request, *args, **kwargs):
        """
            Sub-classes must override this method to do something sensible.
        """
        response_data = {
            'dummy'   : 'some value',
        }
        return self.render_to_json_response(response_data)

    def _message_context(self, success=False):
        return {
            'success' : success,
            'message' : get_template(self.messages_template).render(context={'messages':messages.get_messages(self.request)}),
        }

    def _form_errors_context(self, form, strip_tags=False):
        return {
            'success' : False,
            'errors' : get_template(self.form_errors_template).render(context={'form':form, 'strip_tags':strip_tags})
        }
