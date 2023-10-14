"""
    Test suite for SDE attachment models -- models for the __attach tables associated with some models
"""
from django.test import TestCase, override_settings
from arcsde.attachments import models, forms
from .models import SdeFeatureModel

@override_settings(ROOT_URLCONF='arcsde.tests.urls')
class BaseAttachmentModelTests(TestCase):

    def setUp(self):
        super().setUp()
        self.feature = SdeFeatureModel.objects.create()

    def get_attachment_model(self):
        return models.get_attachment_model(SdeFeatureModel)


class AttachmentModelRegistryTests(BaseAttachmentModelTests):

    def test_attachment_model_registry(self):
        self.assertTrue(models.AttachmentModelRegistry.related_model_in_registry(SdeFeatureModel))

    def test_attachment_related_classes_registry(self):
        self.assertEqual(self.get_attachment_model(), models.AttachmentModelRegistry.get_attachment_model(SdeFeatureModel))


class AttachmentModelTests(BaseAttachmentModelTests):

    def test_related_model_has_attachments(self):
        self.assertTrue(self.feature.has_attachments(),
                                'Model instance %s does not "has_attachments".'%self.feature)
        self.assertTrue(hasattr(self.feature.sde_attachments, 'images'))
        self.assertTrue(hasattr(self.feature.sde_attachments, 'count'))

    def test_attachment_model(self):
        attachment_model = self.get_attachment_model()
        attached_model_name = attachment_model._meta.model_name.lower()
        expected_model_name = models.get_attachment_model_name(SdeFeatureModel).lower()
        self.assertEqual(attached_model_name, expected_model_name, 'SDE Feature AttachmentModel has unexpected name %s'%expected_model_name)

    def test_attachment_model_factory(self):
        attachment_model = self.get_attachment_model()
        fk = attachment_model._meta.get_field('related_object')
        related_model = fk.related_model().__class__
        self.assertEqual(related_model, SdeFeatureModel, 'Attachment related_model does not match creation model.')

    def test_attachment_get_URI(self):
        attachment_model = self.get_attachment_model()
        testImg = attachment_model.get_test_object()
        uri = testImg.get_data_URI()
        self.assertEqual(uri.count('data:image/png;base64,'), 1, 'Attachments get_data_URI did not return valid image data URI')

    def test_image_list_url(self):
        attachment_model = self.get_attachment_model()
        self.feature.pk = 42
        testImg = attachment_model.get_test_object()
        testImg.related_object = self.feature
        testImg.attachmentid = 1
        url = testImg.image_list_url()
        self.assertEqual(url,r'/arcsde/attachments/as_images/arcsde_tests/SdeFeatureModel/42/', 'Attachments image_list_url returned unexpected URL')

    def test_caption_save_url(self):
        attachment_model = self.get_attachment_model()
        self.feature.pk = 42
        testImg = attachment_model.get_test_object()
        testImg.related_object = self.feature
        testImg.attachmentid = 1
        url = testImg.caption_save_url()
        self.assertEqual(url,r'/arcsde/attachments/save/arcsde_tests/SdeFeatureModel/42/1/', 'Attachments get_caption_save_url returned unexpected URL')


class AttachmentsDescriptorApiTests(BaseAttachmentModelTests):

    def test_has_attachments(self):
        self.assertTrue(self.feature.sde_attachments.has_attachments)

    def test_exists(self):
        self.assertFalse(self.feature.sde_attachments.exists)
        self.feature.attachment_count = 2
        self.assertTrue(self.feature.sde_attachments.exists)

    def test_count_query(self):
        self.assertEqual(self.feature.sde_attachments.count, 0)

    def test_count_cached(self):
        self.feature.attachment_count = 42
        self.assertEqual(self.feature.sde_attachments.count, 42)

    def test_images_url(self):
        self.feature.pk = 42
        url = self.feature.sde_attachments.images_url
        self.assertEqual(url,r'/arcsde/attachments/as_images/arcsde_tests/SdeFeatureModel/42/')  # TestModel/42/')

    def test_attachments_model(self):
        self.assertEqual(self.feature.sde_attachments.attachments_model.__name__, 'SdeFeatureModelAttachments') #'TestModelAttachments')


class AttachmentCaptionFormTests(BaseAttachmentModelTests):
    def setUp(self):
        super().setUp()
        self.feature.pk = 42
        self.attachment = self.feature.sde_attachments.attachments_model(related_object=self.feature)
        self.attachment.pk = 99
        self.attachment.att_name = 'original caption'

    def test_unbound_form(self):
        form = forms.CaptionForm(instance=self.attachment)
        self.assertEqual(form.initial['att_name'], self.attachment.att_name)

    def test_bound_form(self):
        new_caption = 'New Caption'
        form = forms.CaptionForm(data={'att_name': new_caption}, instance=self.attachment)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['att_name'], new_caption)
