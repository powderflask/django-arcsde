
from django.urls import path

import arcsde.attachments.views

app_name = "attachments"

# URL Arguments:
# related_model:  Required model class name - identifies which model the attachments are related to
# related_pk:     Required primary key / id - identifies which specific related model the attachments belong to
# attachment_pk:  Attachment primary key / id - identifies which specific attachment to save caption for

# CAUTION: These views are only login-protected -- no other permissions checks applied -- see Design Notes
urlpatterns = [
    path('as_images/<slug:related_model_app>/<slug:related_model>/<int:related_pk>/',
        view = arcsde.attachments.views.AjaxAttachedImagesView.as_view(),
        name = 'images-list-ajax'
    ),
    path('save/<slug:related_model_app>/<slug:related_model>/<int:related_pk>/<int:attachment_pk>/',
        view = arcsde.attachments.views.AjaxAttachedCaptionSave.as_view(),
        name = 'caption-save-ajax'
    ),
]
