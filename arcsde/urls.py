
from django.urls import include, path

app_name = 'arcsde'

urlpatterns = [
    path('attachments/', include('arcsde.attachments.urls')),
]
