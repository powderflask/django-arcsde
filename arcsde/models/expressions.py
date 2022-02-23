"""
    Usefule query expressions for working with SDE models.
"""
from django.db import models
from django.db.models.functions import Coalesce


def sde_attachment_count(model):
    """
        Return a Query Expression providing a count of the number of attachments on each object
        Roughly equivalent to: Count('attachment_set')
         --> broken b/c aggregation on Views with non-primary-key relations broke in django 1.11 -- see https://code.djangoproject.com/ticket/28107
        UPDATE: DEPRECATED -- the issue above is resoved, just use:  Count('attachment_set)
    """
    if model.has_attachments() :

        try:
            attach_model = model.sde_attachments.attachments_model
        except AttributeError:
            from arcsde.attachments.models import get_attachment_model
            attach_model = get_attachment_model(model)

        join_on = 'related_object_id'
        join = {join_on : models.OuterRef('globalid')}
        attachments = attach_model.objects.filter(**join).order_by().values(join_on)
        attachments_count = attachments.annotate(count=models.Count('*')).values('count')
        return Coalesce(models.Subquery(attachments_count), models.Value(0))   # ensure we get a zero, not None
    else:
        return models.Value(0, output_field=models.IntegerField())

    # Roughly equivalent to the RawSQL expression :
    #     raw_query = """
    #       SELECT COUNT(*) FROM {attach_model}
    #           WHERE {attach_model}.rel_globalid = {model}.globalid
    #     """.format(
    #         attach_model=model.sde_attachments.attachments_model._meta.db_table,
    #         model=model._meta.db_table,
    #     )
