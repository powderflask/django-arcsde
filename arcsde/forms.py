from django import forms

#####################################################################
#  Base form class used to share common functionality for SDE report forms.
#  This class is ABSTRACT -- must be sub-classed to be of use!
#####################################################################


class AbstractSdeForm(forms.ModelForm):
    """
        Placeholder in case need for low-level override to all SDE Feature edit forms arises.
    """
    pass
