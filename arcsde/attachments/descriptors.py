from typing import Callable, Optional, TypeAlias

from . import models

AttachmentsApi = models.ArcSdeAttachmentsApi

SdeAttachmentsModel: TypeAlias = type[models.AbstractSdeAttachModel]
SdeModelType: TypeAlias = type[models.AbstractArcSdeBase]
# returns name of related attachments DB table for an SDE feature model
AttachmentDbTableGetter: TypeAlias = Callable[[SdeModelType], str]


class ArcSdeAttachmentsDescriptor:
    """
        A descriptor used to inject ArcSdeAttachmentsApi into an SDE feature instance
        Usage:    sde_attachments = ArcSdeAttachmentsDescriptor()
    """
    attachments_api:type[AttachmentsApi] = AttachmentsApi

    def __init__(self,
                 attachment_model_db_table_name: Optional[str | AttachmentDbTableGetter] = None,
                 attachments_api: Optional[type[AttachmentsApi]] = None):
        """
            Construct a descriptor for the given model_db_table name, None to use SDE default naming conventions

            :param attachment_model_db_table_name: optiional name of a db table or a callable that returns one
            :param attachments_api: optional class that implements ArcSdeAttachmentsApi interface
        """
        self.attachment_model_db_table_name = (
            attachment_model_db_table_name or models.get_attachment_model_db_table_name
        )
        self.attachments_api = attachments_api or type(self).attachments_api

    def __set_name__(self, owner, name):
        self.attachments_attr = name

    def get_attachments_db_table_name(self, sde_feature_model_class: SdeModelType) -> str:
        """
            Return name of the attachments DB table associated with given SDE feature model
        """
        return (
            self.attachment_model_db_table_name(sde_feature_model_class)
            if callable(self.attachment_model_db_table_name) else self.attachment_model_db_table_name
        )

    def get_attachments_model(self, sde_feature_model_class: SdeModelType) -> SdeAttachmentsModel:
        """
            Create, register, and return the SDE attachments model class for the given SDE feature model class
            Reverse relation, attachment_set, is added to sde_feature_model_class by ForeignKey on ConcreteSdeAttachModel
        """
        return models.get_attachment_model(sde_feature_model_class,
                                           self.get_attachments_db_table_name(sde_feature_model_class))

    def __get__(self, instance, owner=None):
        sde_feature_class = instance.__class__ if instance else owner
        attachments_model = self.get_attachments_model(sde_feature_class) if sde_feature_class is not None else None

        if not attachments_model:   # there is no attachments model for this instance
            return None

        if instance is None:  # class access to descriptor - return the concrete attachments model class
            return attachments_model

        # replace the descriptor property on instance with an API instance can use to access its attachments.  Voila!
        attachments_api = self.attachments_api(instance)
        setattr(instance, self.attachments_attr, attachments_api)
        return attachments_api


ArcSdeAttachments = ArcSdeAttachmentsDescriptor   # give it a nicer name
