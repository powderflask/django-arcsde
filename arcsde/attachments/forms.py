from django import forms

""" ******** Generic Caption editing form for SDE Attachment models **********"""

class CaptionForm(forms.Form):
    """
        A simple form for editing an Attachment caption.
        This is actually a model form, but works with instances from ANY attachments.models.AttachmentModelRegistry
    """
    att_name = forms.CharField(max_length=250, widget=forms.Textarea(attrs={'rows':'2'}))

    def __init__(self, instance, *args, **kwargs):
        super().__init__(initial={'att_name': instance.att_name}, *args, **kwargs)
        self.instance = instance

    def save(self):
        if self.is_valid():
            self.instance.att_name = self.cleaned_data['att_name']
            self.instance.save(update_fields=['att_name'])  # this implies force_update=True
            return self.instance
        return False

