
import arcsde.tz
from django import template
from django.template.defaultfilters import date
from django.template.loader import get_template
register = template.Library()

@register.filter
def report_version_info(sde_feature_instance):
    """ Returns report version info rendered in HTM for the given arcsde.models.AbstractArcSdeFeature instance """
    info_template = get_template('arcsde/tags/report_version_info.html')
    try:
        return info_template.render(sde_feature_instance.get_report_version_info())
    except AttributeError:
        return ''


@register.filter(expects_localtime=True, is_safe=False)
def localize_date(value, arg=None):
    """ Format a UTC date from SDE as local PST time, according to the given format. """
    value = arcsde.tz.localize(value)
    return date(value, arg)


@register.inclusion_tag('arcsde/attachments/caption_editable.html')
def attachment_caption(attachment):
    return {
        'caption_id': 'Caption-{id}'.format(id=attachment.pk),
        'form_action': attachment.caption_save_url,
        'form_id': 'CaptionEditForm-{id}'.format(id=attachment.pk),
        'attachment': attachment,
    }
