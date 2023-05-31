from django.apps import AppConfig


class ArcSdeConfig(AppConfig):
    name = 'arcsde'
    verbose_name = "Arc SDE Infrastructure app"

# This would be a good idea, except: slows down django startup in DEV & preempts create_sde_attach_tables_receiver in test/apps
# For now, each app needs to ensure it accesses Model.sde_attachments before it tries to e.g., make a prefetch query.
#     def ready(self):
#         create_sde_attach_models()
#
#
# def create_sde_attach_models(descriptor='sde_attachments'):
#     """ Create SDE __attach tables for any model classes with an ArcSdeAttachmentsDescriptor descriptor """
#     for model in apps.get_models():
#         # Only need to touch the descriptor to trigger model creation.
#         getattr(model, descriptor, None)
