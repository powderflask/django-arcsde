import logging

from django import forms
from django.core.exceptions import ValidationError

from . import settings

logger = logging.getLogger('arcsde')


class SdeVersionField(forms.DateTimeField):
    """
    A hidden field used to guard against concurrency issues on SDE features
    Usage:
        inherit from AbstractSdeForm;
        add 'last_edited_date' to form.Meta.fields
        --> a validation error will be raised if a concurrency issue is detected
    """
    widget = forms.HiddenInput

    def __init__(self, **kwargs):
        """ By default, the version field is not required - if left out, no concurrency checks are performed. """
        kwargs.setdefault('required', False)
        super().__init__(**kwargs)


#####################################################################
#  Base form class used to share common functionality for SDE report forms.
#  This class is ABSTRACT -- must be sub-classed to be of use!
#####################################################################


class AbstractSdeForm(forms.ModelForm):
    """
        Low-level functionality added to all SDE Feature edit forms.

        Adds concurrency detection using "optimistic lock" algorithm,
            using SDE `last_edited_date` field for versioning (if model has SDE revision fields)
        Concurrency errors are raised as non-field errors on the form.
    """
    concurrency_lock_field = 'last_edited_date'  # version field for optimistic lock
    last_edited_date = SdeVersionField()

    def __init__(self, *args, initial=None, **kwargs):
        """ Configure the initial value for lock field, since field is not expected to be included in Meta.fields """
        initial = initial or {}
        instance = kwargs.get('instance')
        if hasattr(instance, self.concurrency_lock_field):
            initial.setdefault(self.concurrency_lock_field, getattr(instance, self.concurrency_lock_field))
        super().__init__(*args, initial=initial, **kwargs)

    def clean(self):
        """ SDE feature-specific validation. """
        cleaned_data = super().clean()
        self._concurrency_validation(cleaned_data)
        return cleaned_data

    def _concurrency_validation(self, form_data):
        """
        Use optimistic locking strategy to detect concurrency issues

        Concurrency validation is applied only if form.instance has a `last_edited_date` field and
        a value for that field is in the cleaned_data.
        Any edit form for an AbstractArcSdeFeature instance that extends this one will inherit the concurrency check.

        This approach should catch concurrency issues in a system with relatively small number
        of users, where simultaneous editing of same data by different users is fairly rare.
        Though statistically unlikely, this lock can miss near-simultaneous concurrency issues

        disable with settings.SDE_CONCURRENCY_LOCK = False
        """
        version_timestamp = form_data.get(self.concurrency_lock_field)
        version_pk = form_data.get(self.instance._meta.pk.name, False)
        if not _optimistic_lock(
            self.instance,
            self.concurrency_lock_field,
            version_timestamp=version_timestamp,
            version_pk=version_pk,
        ):
            msg = "Feature was removed in Map or another browser tab." \
                if version_pk and not self.instance.pk  else \
                  "Data was modified in Map or another browser tab."
            raise ValidationError(f'Concurrent feature edit detected. {msg}')


def same_instance(form_instance, form_pk_data):
    """ Django converts form PK data into an instance... sometimes.  Return True if 2 items represent same instance """
    return form_instance == form_pk_data or (form_instance and form_instance.pk == form_pk_data)

def _optimistic_lock(model_instance, version_field, version_timestamp, version_pk=False):
    """
    Return True iff the model instance has not been modified since version_timestamp

    if version_pk is passed in, also check that model_instance was not previously deleted

    model_instance has been modified if:
        the version timestamp differs (i.e., the instance was updated prior to form post); or
        the instance.pk differs from version_pk  (i.e., instance was deleted prior to form post)
    """
    if not settings.SDE_CONCURRENCY_LOCK:
        return True

    # if form data includes version field, verify version matches instance.
    version_matches = not version_timestamp or getattr(model_instance, version_field) == version_timestamp

    # if form data includes version pk field, verify pk matches instance.
    pk_matches = version_pk is False or same_instance(model_instance, version_pk)

    if version_matches and pk_matches:
        # "lock" obtained - form data version matches model instance version.
        return True

    # "lock" could not be obtained - the model instance has been modified or deleted between form get and form post
    logger.debug(f"Concurrency conflict detected on `{model_instance}` pk:`{model_instance.pk}`, "
                 "version `{value}` was modified.")
    return False
