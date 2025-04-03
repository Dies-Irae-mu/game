from django import forms
from .models import Job, Queue, JobTemplate, JobAttachment
from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB

class JobForm(forms.ModelForm):
    """Form for creating and editing jobs."""
    title = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}))
    queue = forms.ModelChoiceField(queryset=Queue.objects.all())
    assignee = forms.ModelChoiceField(queryset=AccountDB.objects.all(), required=False)
    participants = forms.ModelMultipleChoiceField(queryset=AccountDB.objects.all(), required=False)
    due_date = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}))
    template = forms.ModelChoiceField(queryset=JobTemplate.objects.all(), required=False)
    template_args = forms.JSONField(required=False, widget=forms.HiddenInput())
    comments = forms.JSONField(required=False, widget=forms.HiddenInput())
    attached_objects = forms.ModelMultipleChoiceField(queryset=ObjectDB.objects.all(), required=False)

    class Meta:
        model = Job
        fields = ['title', 'description', 'queue', 'assignee', 'participants', 
                 'due_date', 'template', 'template_args', 'comments', 'attached_objects']
        exclude = ['id', 'archive_id', 'requester', 'created_at', 'updated_at', 
                  'closed_at', 'status', 'approved', 'last_viewed']

    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values
        if self.requester:
            self.fields['requester'].initial = self.requester
            self.fields['status'].initial = 'open'
            self.fields['comments'].initial = []
            self.fields['template_args'].initial = {}
            self.fields['last_viewed'].initial = {}

class QueueForm(forms.ModelForm):
    """Form for creating and editing queues."""
    class Meta:
        model = Queue
        fields = ['name', 'automatic_assignee']

class JobTemplateForm(forms.ModelForm):
    """Form for creating and editing job templates."""
    class Meta:
        model = JobTemplate
        fields = ['name', 'queue', 'close_commands', 'args']
        widgets = {
            'close_commands': forms.Textarea(attrs={'rows': 4}),
            'args': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_args(self):
        """Validate that args is valid JSON."""
        args = self.cleaned_data.get('args')
        try:
            import json
            if isinstance(args, str):
                args = json.loads(args)
            return args
        except json.JSONDecodeError:
            raise forms.ValidationError("Args must be valid JSON")

class JobAttachmentForm(forms.ModelForm):
    """Form for attaching objects to jobs."""
    class Meta:
        model = JobAttachment
        fields = ['job', 'object', 'attached_to_arg']
        widgets = {
            'job': forms.HiddenInput(),
            'attached_to_arg': forms.TextInput(attrs={'placeholder': 'Template argument (optional)'}),
        }

class JobCommentForm(forms.Form):
    """Form for adding comments to jobs."""
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    author = forms.ModelChoiceField(queryset=AccountDB.objects.all(), widget=forms.HiddenInput())
    created_at = forms.DateTimeField(widget=forms.HiddenInput()) 