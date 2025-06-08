from functools import cached_property

from django.apps import apps
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.shortcuts import get_object_or_404

from arcsde.views import AjaxOnlyView
from arcsde.attachments.models import AttachmentModelRegistry
from arcsde.attachments.forms import CaptionForm

# CAUTION: These views are only login-protected -- no other permissions checks applied -- see Design Notes


class BaseAttachmentViewMixin:
    kwargs = None  # must be mixed in with view class that provides kwargs

    def _get_attachment_model(self):
        """
        Lookup the attachments model from the related_model_class.
        :return: the attachments model class for the related model
        """
        related_class = self._get_related_model_class()
        if not getattr(related_class, 'has_attachments', lambda:False)():  #  Important! ensure dynamic class exists
            raise Http404

        attachments_model = AttachmentModelRegistry.get_attachment_model(related_class)
        if not attachments_model:
            raise Http404

        return attachments_model

    def _get_related_model_class(self):
        """
        Lookup the object related to the attachments based on 'related_model_app', 'related_model' names in view kwargs.
        :return: the model class defined by the related_model and related_pk URL parameters.
        """
        related_model_app = self.kwargs.get('related_model_app', None)
        related_model_name = self.kwargs.get('related_model', None)
        return apps.get_model(related_model_app, related_model_name)

    def _get_related_object(self):
        """
        Lookup the object related to the attachments based on 'related_pk' in view kwargs.
        This object is needed to fetch related attachments by globalid, which is the relational FK.
        :return: the object defined by the related_model and related_pk URL parameters.
        """
        related_pk = self.kwargs.get('related_pk', None)
        related_class = self._get_related_model_class()
        # special case: handle view that may contain duplicate records (e.g., multi-circuit patrols)
        related_object = related_class.objects.filter(pk=related_pk).first() if related_class and related_pk else None

        if not related_object:
            raise Http404

        return related_object

    @cached_property
    def related_object(self):
        return self._get_related_object()

    def _get_attachments_qs(self):
        """ returns queryset for SDE attachments defined by the kwargs """
        # roughly equivalent to: self._get_related_object().attachment_set.all()
        # use the explicit form below too ensure the attachment model is dynamically created
        return self._get_attachment_model().objects.filter(related_object=self.related_object)

    @cached_property
    def attachments_qs(self):
        return self._get_attachments_qs()


class AjaxAttachedImagesView(BaseAttachmentViewMixin, AjaxOnlyView):
    """
        Get all image attachments related the model specified in the URL
        Return as a set of HTML .item elements, intended to be loaded to a target viewer on the client-side
    """
    image_tag_template = get_template("arcsde/attachments/as_modal_image_item.html")

    def get(self, request, *args, **kwargs):
        # Format results as a set of HTML image tags
        return HttpResponse("\n".join(self.get_image_tags(request)))

    def get_image_attachments(self):
        return super().attachments_qs.sde_image_attachments()

    @cached_property
    def attachments_qs(self):
        return self.get_image_attachments()

    def get_image_tags(self, request) -> list:
        """
            Format all of the images attached to related_object as HTML image tags
        """
        # Filter for image-type attachments
        attachments_qs = self.get_image_attachments()

        return [
            self.image_tag_template.render(context={'attachment': a, 'caption_form': CaptionForm(a)}, request=request)
            for a in attachments_qs
        ]


class AjaxAttachedCaptionSave(BaseAttachmentViewMixin, AjaxOnlyView):
    """
        Save the image caption related to the model specified in the URL
    """
    def post(self, request, *args, **kwargs):
        attachment_pk = self.kwargs.get('attachment_pk', None)

        # Get THE attachment, Save the form
        attachment = get_object_or_404(self.attachments_qs, pk=attachment_pk)
        caption_form = CaptionForm(attachment, data=request.POST)
        updated_attachment = caption_form.save()
        if updated_attachment:
            return self.render_to_json_response({'success':True, 'caption_text': updated_attachment.att_name})
        else:
            return self.render_to_json_response(self._form_errors_context(caption_form))
