"""
SDE Attachment model managers and querysets
@author: powderflask
"""
from arcsde.models import managers

class SdeAttachmentQuerySet(managers.ArcSdeQuerySet):
    """
        Adds methods specific to Arc Attachments (__attach models)
    """
    def sde_image_attachments(self):
        """
            Filter attachments to only image content types
        """
        return self.filter(content_type__contains='image')


SdeAttachmentManager = managers.ArcSdeManager.from_queryset(SdeAttachmentQuerySet, class_name='SdeAttachmentManager')
