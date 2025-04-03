from django.contrib import admin
from django import forms
from django.utils import timezone
from .models import Job, Queue, JobTemplate, JobAttachment, ArchivedJob
from django.utils.html import mark_safe
import re
import json

def convert_ansi_to_html(text):
    """Convert ANSI codes to HTML spans with appropriate classes."""
    # Replace common ANSI patterns with HTML
    replacements = {
        '|n': '</span>',  # Reset
        '|w': '<span class="ansi-white">',  # White
        '|r': '<span class="ansi-red">',    # Red
        '|g': '<span class="ansi-green">',  # Green
        '|b': '<span class="ansi-blue">',   # Blue
        '|y': '<span class="ansi-yellow">', # Yellow
        '|c': '<span class="ansi-cyan">',   # Cyan
        '|m': '<span class="ansi-magenta">', # Magenta
    }
    
    # Convert each ANSI code to its HTML equivalent
    result = text
    for ansi, html in replacements.items():
        result = result.replace(ansi, html)
    
    # Ensure all spans are properly closed
    open_spans = result.count('<span')
    close_spans = result.count('</span>')
    if open_spans > close_spans:
        result += '</span>' * (open_spans - close_spans)
    
    return result

class JobAdminForm(forms.ModelForm):
    new_comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'new-comment-form',
            'placeholder': 'Enter your comment here. Press Enter for new lines.'
        }),
        required=False,
    )

    class Meta:
        model = Job
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields not required
        self.fields['template_args'].required = False
        self.fields['comments'].required = False
        self.fields['last_viewed'].required = False
        
        # Set default values for fields that should never be empty
        if not self.instance.template_args:
            self.instance.template_args = {}
        if not self.instance.comments:
            self.instance.comments = []
        if not self.instance.last_viewed:
            self.instance.last_viewed = {}

        # Format existing comments for display
        if self.instance.pk:
            self.instance.formatted_comments = []
            if self.instance.comments:
                for comment in self.instance.comments:
                    # Replace %r with actual newlines for display
                    text = comment['text'].replace('%r', '\n')
                    self.instance.formatted_comments.append({
                        'text': text,
                        'author': comment['author'],
                        'created_at': comment['created_at']
                    })

    def clean(self):
        cleaned_data = super().clean()
        # Ensure template_args is a dict
        if not cleaned_data.get('template_args'):
            cleaned_data['template_args'] = {}
        # Ensure comments is a list
        if not cleaned_data.get('comments'):
            cleaned_data['comments'] = []
        # Ensure last_viewed is a dict
        if not cleaned_data.get('last_viewed'):
            cleaned_data['last_viewed'] = {}
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle new comment if provided
        new_comment = self.cleaned_data.get('new_comment')
        if new_comment:
            # Convert newlines to %r for MUSH compatibility
            formatted_text = new_comment.replace('\n', '%r')
            
            if not instance.comments:
                instance.comments = []
                
            # Add the new comment
            instance.comments.append({
                'author': 'Admin',
                'text': formatted_text,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            })

            # Update last_viewed timestamp for admin
            if not instance.last_viewed:
                instance.last_viewed = {}
            instance.last_viewed['admin'] = timezone.now().isoformat()
        
        if commit:
            instance.save()
        return instance

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    form = JobAdminForm
    list_display = ('id', 'title', 'queue', 'requester', 'assignee', 'status', 'created_at', 'closed_at')
    list_filter = ('status', 'queue', 'created_at', 'closed_at')
    search_fields = ('title', 'description', 'requester__username', 'assignee__username')
    raw_id_fields = ('requester', 'assignee', 'participants')
    readonly_fields = ('created_at', 'updated_at', 'formatted_comments')
    date_hierarchy = 'created_at'
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.current_user = request.user
        return form

    def formatted_comments(self, obj):
        if not hasattr(obj, 'formatted_comments'):
            return "No comments"
        
        html = '<div class="job-comments">'
        for i, comment in enumerate(obj.formatted_comments, 1):
            html += '<div class="comment-box">'
            html += f'<div class="comment-header">Comment {i}</div>'
            html += f'<div class="comment-meta">By {comment["author"]} on {comment["created_at"]}</div>'
            html += '<div class="comment-text">'
            
            # Handle roll results and warnings specially
            text = comment["text"]
            if "Roll Result:" in text or "Warning:" in text:
                lines = text.split('\n')
                for line in lines:
                    if line.startswith("Roll Result:"):
                        html += f'<div class="roll-result">{convert_ansi_to_html(line)}</div>'
                    elif line.startswith("Warning:"):
                        html += f'<div class="warning-message">{convert_ansi_to_html(line)}</div>'
                    else:
                        html += convert_ansi_to_html(line) + '<br>'
            else:
                html += convert_ansi_to_html(text)
            
            html += '</div></div>'
        
        html += '</div>'
        return mark_safe(html)
    
    formatted_comments.short_description = "Comments"
    formatted_comments.allow_tags = True

    class Media:
        css = {
            'all': ('jobs/css/jobs_admin.css',)
        }

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ('name', 'automatic_assignee')
    search_fields = ('name',)
    raw_id_fields = ('automatic_assignee',)

@admin.register(JobTemplate)
class JobTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'queue')
    list_filter = ('queue',)
    search_fields = ('name',)

@admin.register(JobAttachment)
class JobAttachmentAdmin(admin.ModelAdmin):
    list_display = ('job', 'object', 'attached_to_arg')
    list_filter = ('job__queue',)
    search_fields = ('job__title', 'object__db_key')
    raw_id_fields = ('job', 'object')

@admin.register(ArchivedJob)
class ArchivedJobAdmin(admin.ModelAdmin):
    list_display = ('original_id', 'archive_id', 'title', 'queue', 'requester', 'assignee', 'status', 'created_at', 'closed_at')
    list_filter = ('status', 'queue', 'created_at', 'closed_at')
    search_fields = ('title', 'description', 'requester__username', 'assignee__username')
    raw_id_fields = ('requester', 'assignee', 'queue')
    readonly_fields = ('created_at', 'closed_at')
    date_hierarchy = 'created_at' 