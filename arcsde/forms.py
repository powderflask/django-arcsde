from django import forms

#####################################################################
#  Base form class used to share common functionality for SDE report forms.
#  This class is ABSTRACT -- must be sub-classed to be of use!
#####################################################################


class AbstractSdeForm(forms.ModelForm):
    """
        Uses SDE revision tracking fields to leave an audit trail when form is saved.
        Ideally this would be done at the model level... but how to get request.user there at right moment?
    """
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # we need the user to track revisions (audit trail) during save
        super().__init__(*args, **kwargs)

    def set_user(self, user):
        """ Set the auth.user who is modifying this form to leave last_edited audit trail on save """
        self.user = user

    def save(self, commit=True):
        """ Try to update the revision / audit trail (last_edited_user) for the model being saved """
        try:
            self.instance.update_edited_by(self.user.username) if self.user else None
        except AttributeError:
            pass
        # May also want to exclude writing shape fields here?

        return super().save(commit)