"""
Forms for managing situations and their components.
"""

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from world.situations.models import Situation, Detail, Development
from world.jobs.models import Job
from world.plots.models import Plot
from world.wod20th.models import Roster

class SituationForm(forms.ModelForm):
    """Form for creating and editing situations."""
    roster_names = forms.ModelMultipleChoiceField(
        queryset=Roster.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Rosters", False),
        help_text="Leave empty to make the situation visible to everyone."
    )
    related_plots = forms.ModelMultipleChoiceField(
        queryset=Plot.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Plots", False)
    )
    job_id = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter Job ID'}),
        help_text="Enter a job ID to link it to this situation."
    )

    class Meta:
        model = Situation
        fields = ['title', 'description', 'roster_names', 'related_plots', 'staff_notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10}),
            'staff_notes': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_id'].label = "Add Job by ID"
        
        # If we have an instance, get its related jobs for the template
        if self.instance.pk:
            self.related_jobs = self.instance.related_jobs.all().select_related('creator').order_by('id')
        else:
            self.related_jobs = []

    def clean_job_id(self):
        job_id = self.cleaned_data.get('job_id')
        if job_id:
            try:
                job = Job.objects.get(id=job_id)
                return job
            except Job.DoesNotExist:
                raise forms.ValidationError(f"Job with ID {job_id} does not exist.")
        return None

    def clean_roster_names(self):
        """Convert the roster QuerySet to a list of roster names."""
        rosters = self.cleaned_data.get('roster_names')
        if rosters:
            return [roster.name for roster in rosters]
        return []

    def save(self, commit=True):
        """Override save to handle roster_names properly."""
        instance = super().save(commit=False)
        instance.roster_names = self.cleaned_data.get('roster_names', [])
        if commit:
            instance.save()
            self.save_m2m()  # Save many-to-many relationships
        return instance

class DetailForm(forms.ModelForm):
    """Form for creating and editing details."""
    roster_names = forms.ModelMultipleChoiceField(
        queryset=Roster.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Rosters", False),
        help_text="Leave empty to inherit situation's visibility."
    )

    class Meta:
        model = Detail
        fields = ['title', 'content', 'roster_names', 'secrecy_rating', 'staff_notes']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'staff_notes': forms.Textarea(attrs={'rows': 5}),
        }

class DevelopmentForm(forms.ModelForm):
    """Form for creating and editing developments."""
    roster_names = forms.ModelMultipleChoiceField(
        queryset=Roster.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("Rosters", False),
        help_text="Leave empty to inherit situation's visibility."
    )

    class Meta:
        model = Development
        fields = ['title', 'content', 'roster_names', 'resolved', 'resolution_text', 'staff_notes']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'resolution_text': forms.Textarea(attrs={'rows': 5}),
            'staff_notes': forms.Textarea(attrs={'rows': 5}),
        } 