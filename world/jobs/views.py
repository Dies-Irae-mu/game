from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from .models import Job, Queue, JobTemplate, JobAttachment, ArchivedJob
from .forms import JobForm, QueueForm, JobTemplateForm, JobAttachmentForm, JobCommentForm
from evennia.accounts.models import AccountDB
from evennia.objects.models import ObjectDB

@login_required
def job_list(request):
    """List all jobs."""
    if request.user.check_permstring("Admin"):
        jobs = Job.objects.filter(status__in=['open', 'claimed']).order_by('-created_at')
    else:
        jobs = Job.objects.filter(
            Q(requester=request.user) |
            Q(participants=request.user),
            status__in=['open', 'claimed']
        ).distinct().order_by('-created_at')
    
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

@login_required
def job_detail(request, pk):
    """View details of a specific job."""
    job = get_object_or_404(Job, pk=pk)
    
    # Check permissions
    if not request.user.check_permstring("Admin") and \
       job.requester != request.user and \
       job.assignee != request.user and \
       request.user not in job.participants.all():
        messages.error(request, "You don't have permission to view this job.")
        return redirect('job_list')
    
    # Mark job as viewed
    job.mark_viewed(request.user)
    
    # Handle comment submission
    if request.method == 'POST' and 'comment' in request.POST:
        comment_form = JobCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.author = request.user
            comment.created_at = timezone.now()
            
            if not job.comments:
                job.comments = []
            job.comments.append({
                'author': request.user.username,
                'text': comment.text,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
            job.save()
            messages.success(request, 'Comment added successfully.')
            return redirect('job_detail', pk=pk)
    else:
        comment_form = JobCommentForm()
    
    # Handle object attachment
    if request.method == 'POST' and 'attach_object' in request.POST:
        attachment_form = JobAttachmentForm(request.POST)
        if attachment_form.is_valid():
            attachment = attachment_form.save(commit=False)
            attachment.job = job
            attachment.save()
            messages.success(request, 'Object attached successfully.')
            return redirect('job_detail', pk=pk)
    else:
        attachment_form = JobAttachmentForm(initial={'job': job})
    
    return render(request, 'jobs/job_detail.html', {
        'job': job,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
    })

@login_required
def job_create(request):
    """Create a new job."""
    if request.method == 'POST':
        form = JobForm(request.POST, requester=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.requester = request.user
            job.status = 'open'
            job.save()
            
            # Handle many-to-many relationships
            form.save_m2m()
            
            messages.success(request, f'Job #{job.id} created successfully.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm(requester=request.user)
    
    return render(request, 'jobs/job_form.html', {'form': form})

@login_required
def job_edit(request, pk):
    """Edit an existing job."""
    job = get_object_or_404(Job, pk=pk)
    
    # Check permissions
    if not request.user.check_permstring("Admin") and job.requester != request.user:
        messages.error(request, "You don't have permission to edit this job.")
        return redirect('job_detail', pk=pk)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job, requester=job.requester)
        if form.is_valid():
            job = form.save()
            form.save_m2m()
            messages.success(request, f'Job #{job.id} updated successfully.')
            return redirect('job_detail', pk=job.pk)
    else:
        form = JobForm(instance=job, requester=job.requester)
    
    return render(request, 'jobs/job_form.html', {'form': form, 'job': job})

@login_required
def job_claim(request, pk):
    """Claim a job."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to claim jobs.")
        return redirect('job_detail', pk=pk)
    
    job = get_object_or_404(Job, pk=pk)
    if job.status != 'open':
        messages.error(request, "This job is not open for claiming.")
        return redirect('job_detail', pk=pk)
    
    job.assignee = request.user
    job.status = 'claimed'
    job.save()
    
    messages.success(request, f'Job #{job.id} claimed successfully.')
    return redirect('job_detail', pk=pk)

@login_required
def job_close(request, pk):
    """Close a job."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to close jobs.")
        return redirect('job_detail', pk=pk)
    
    job = get_object_or_404(Job, pk=pk)
    if job.status in ['closed', 'rejected']:
        messages.error(request, f"Job #{job.id} is already {job.status}.")
        return redirect('job_detail', pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        is_approved = 'approve' in request.POST
        job.approved = is_approved
        success, subject, message, recipients = job.close(request.user, reason)
        
        if success:
            status = "closed" if is_approved else "rejected"
            messages.success(request, f'Job #{job.id} has been {status} and archived.')
        else:
            messages.error(request, f'Job #{job.id} is already closed or rejected.')
    
    return redirect('job_detail', pk=pk)

@login_required
def job_archive(request):
    """View archived jobs."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to view archived jobs.")
        return redirect('job_list')
    
    archived_jobs = ArchivedJob.objects.all().order_by('-closed_at')
    return render(request, 'jobs/job_archive.html', {'archived_jobs': archived_jobs})

@login_required
def job_archive_detail(request, pk):
    """View details of an archived job."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to view archived jobs.")
        return redirect('job_list')
    
    archived_job = get_object_or_404(ArchivedJob, pk=pk)
    return render(request, 'jobs/job_archive_detail.html', {'job': archived_job})

@login_required
def queue_list(request):
    """List all queues."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to view queues.")
        return redirect('job_list')
    
    queues = Queue.objects.all()
    return render(request, 'jobs/queue_list.html', {'queues': queues})

@login_required
def queue_create(request):
    """Create a new queue."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to create queues.")
        return redirect('queue_list')
    
    if request.method == 'POST':
        form = QueueForm(request.POST)
        if form.is_valid():
            queue = form.save()
            messages.success(request, f'Queue "{queue.name}" created successfully.')
            return redirect('queue_list')
    else:
        form = QueueForm()
    
    return render(request, 'jobs/queue_form.html', {'form': form})

@login_required
def queue_edit(request, pk):
    """Edit an existing queue."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to edit queues.")
        return redirect('queue_list')
    
    queue = get_object_or_404(Queue, pk=pk)
    if request.method == 'POST':
        form = QueueForm(request.POST, instance=queue)
        if form.is_valid():
            queue = form.save()
            messages.success(request, f'Queue "{queue.name}" updated successfully.')
            return redirect('queue_list')
    else:
        form = QueueForm(instance=queue)
    
    return render(request, 'jobs/queue_form.html', {'form': form, 'queue': queue})

@login_required
def template_list(request):
    """List all job templates."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to view templates.")
        return redirect('job_list')
    
    templates = JobTemplate.objects.all()
    return render(request, 'jobs/template_list.html', {'templates': templates})

@login_required
def template_create(request):
    """Create a new job template."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to create templates.")
        return redirect('template_list')
    
    if request.method == 'POST':
        form = JobTemplateForm(request.POST)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template "{template.name}" created successfully.')
            return redirect('template_list')
    else:
        form = JobTemplateForm()
    
    return render(request, 'jobs/template_form.html', {'form': form})

@login_required
def template_edit(request, pk):
    """Edit an existing job template."""
    if not request.user.check_permstring("Admin"):
        messages.error(request, "You don't have permission to edit templates.")
        return redirect('template_list')
    
    template = get_object_or_404(JobTemplate, pk=pk)
    if request.method == 'POST':
        form = JobTemplateForm(request.POST, instance=template)
        if form.is_valid():
            template = form.save()
            messages.success(request, f'Template "{template.name}" updated successfully.')
            return redirect('template_list')
    else:
        form = JobTemplateForm(instance=template)
    
    return render(request, 'jobs/template_form.html', {'form': form, 'template': template})

@login_required
def search_objects(request):
    """AJAX endpoint for searching objects to attach to jobs."""
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'results': []})
    
    objects = ObjectDB.objects.filter(db_key__icontains=query)[:10]
    results = [{'id': obj.id, 'name': obj.key} for obj in objects]
    return JsonResponse({'results': results}) 