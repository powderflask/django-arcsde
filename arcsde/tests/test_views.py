"""
    Test suite for SDE attachment views
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from .test_attachments import BaseAttachmentModelTests
from .models import mock_globalid


def get_user(first_name="Big", last_name="Bird", email="bigbird@example.com",
             username="bbird", password="password", **kwargs):
    """ Return a user object with given attributes """
    user, _ = get_user_model().objects.get_or_create(username=username,
                                                     first_name=first_name, last_name=last_name,
                                                     email=email, **kwargs)
    user.set_password(password)
    user.save()
    return user


def login(client):
    """ create a user and login to client """
    u = get_user()
    client.login(username=u.username, password='password')


class AttachmentsViewsTests(BaseAttachmentModelTests):

    def setUp(self):
        super().setUp()
        self.feature.save()
        model = self.get_attachment_model()
        self.attachment = model.get_test_object()
        self.attachment.related_object = self.feature
        self.attachment.globalid = mock_globalid()
        self.attachment.save()

    def get_images_list_url(self):
        return reverse('arcsde:attachments:images-list-ajax',
                      kwargs={'related_model_app':'arcsde_tests', 'related_model':'SdeFeatureModel', 'related_pk':self.feature.pk})

    def get_caption_save_url(self):
        return reverse('arcsde:attachments:caption-save-ajax',
                      kwargs={'related_model_app':'arcsde_tests', 'related_model':'SdeFeatureModel', 'related_pk':self.feature.pk,
                              'attachment_pk':self.attachment.pk})

    def test_AjaxAttachedImagesView(self):
        c = Client()
        login(c)
        url = self.get_images_list_url()
        response = c.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        attached = response.context['attachment']
        self.assertEqual(attached.pk, self.attachment.pk)
        self.assertIsNotNone(attached.caption_form)
        self.assertIn(b'<img src="data:image/png;base64,', response.content)
        self.assertIn(bytes('<form action="{}"'.format(self.get_caption_save_url()),encoding='utf-8'), response.content)
        # print(response.content)

    def test_AjaxAttachedCaptionSave(self):
        c = Client()
        login(c)
        url = self.get_caption_save_url()
        new_caption = 'New Caption Text'
        response = c.post(url, data={'att_name':new_caption},
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['caption_text'], new_caption)
        attached = self.get_attachment_model().objects.get(pk=self.attachment.pk)
        self.assertEqual(attached.att_name, new_caption)
