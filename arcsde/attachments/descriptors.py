from . import models


class ArcSdeAttachmentsDescriptor:
    """
        A descriptor used to inject ArcSdeAttachmentsApi into an SDE feature instance
        Usage:    sde_attachments = ArcSdeAttachmentsDescriptor()
    """

    def __init__(self,  attachment_model_db_table_name=None):
        """
            Construct a descriptor for the given model_db_table name, None to use SDE default naming conventions
        """
        self.attachment_model_db_table_name = attachment_model_db_table_name

    def __set_name__(self, owner, name):
        self.attachments_attr = name

    def get_attachments_db_table_name(self, sde_feature_model_class):
        """
            Return name of the attachments DB table associated with given SDE feature model
        """
        return self.attachment_model_db_table_name or models.get_attachment_model_db_table_name(sde_feature_model_class)

    def get_attachments_model(self, sde_feature_model_class):
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
        attachments_api = models.ArcSdeAttachmentsApi(instance)
        setattr(instance, self.attachments_attr, attachments_api)
        return attachments_api


ArcSdeAttachments = ArcSdeAttachmentsDescriptor   # give it a nicer name
