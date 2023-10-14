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


# TODO: consider re-factoring JSON views as suggested: https://docs.djangoproject.com/en/3.2/topics/class-based-views/mixins/#more-than-just-html
class AjaxOnlyView(JSONResponseMixin, generic.base.ContextMixin, generic.base.View):
    """ A generic View with a JSON response  """

    messages_template = "arcsde/ajax/messages.html"
    form_errors_template = "arcsde/ajax/form_errors.html"

    def get(self, request, *args, **kwargs):
        """
            Sub-classes must override this method to do something sensible.
        """
        response_data = {
            'dummy'   : 'some value',
        }
        return self.render_to_json_response(response_data)

    def get_error_context(self, msg, form):
        """ Return some context for error tracing - user is only shown a simple msg since no user-fixable errors """
        messages.add_message(self.request, messages.ERROR, msg)
        return {**self._message_context(), **self._form_errors_context(form)}

    def get_messages(self):
        """ Return formatted messages for any messages in the queue - side-effect: clear message queue! """
        return get_template(self.messages_template).render(context={'messages':messages.get_messages(self.request)})

    def _message_context(self, success=False):
        return {
            'success' : success,
            'message' : self.get_messages(),
        }

    def get_form_errors(self, form, strip_tags=False):
        """ Return formatted form_errors using the form_errors_template """
        return get_template(self.form_errors_template).render(context={'form':form, 'strip_tags':strip_tags})

    def _form_errors_context(self, form, strip_tags=False):
        return {
            'success' : False,
            'errors' : self.get_form_errors(form, strip_tags)
        }
