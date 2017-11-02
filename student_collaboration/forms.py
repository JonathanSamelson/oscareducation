from django import forms

from .models import StudentCollaborator, CollaborativeSettings


class StudentCollaboratorForm(forms.ModelForm):
    class Meta:
        model = StudentCollaborator
        fields = ['postal_code', 'collaborative_tool']


class CollaborativeSettingsForm(forms.ModelForm):
    class Meta:
        model = CollaborativeSettings
        fields = ['distance']


class UnmasteredSkillsForm(forms.Form):
    def __init__(self, qs=None, *args, **kwargs):
        super(UnmasteredSkillsForm, self).__init__(*args, **kwargs)
        if qs:
            self.fields['liste'] = forms.ModelMultipleChoiceField(queryset=qs)

