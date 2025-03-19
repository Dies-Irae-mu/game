"""
Views for managing situations and their components.
"""

from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from world.situations.models import Situation, Detail, Development
from world.situations.forms import SituationForm, DetailForm, DevelopmentForm
from world.wod20th.models import RosterMember
from world.jobs.models import Job

class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to require staff access."""
    def test_func(self):
        return self.request.user.is_staff

class SituationAccessMixin:
    """Mixin to check situation access."""
    def has_access(self, situation):
        user = self.request.user
        if user.is_staff:
            return True
        if not situation.roster_names:
            return True
        return RosterMember.objects.filter(
            roster__name__in=situation.roster_names,
            character__account=user,
            approved=True
        ).exists()

class SituationFormMixin:
    """Mixin for handling job relationships in situation forms."""
    def form_valid(self, form):
        response = super().form_valid(form)
        job = form.cleaned_data.get('job_id')
        if job:
            self.object.related_jobs.add(job)
            messages.success(self.request, f'Job #{job.id} "{job.title}" has been linked to this situation.')
        return response

class SituationListView(LoginRequiredMixin, ListView):
    """List all situations the user has access to."""
    model = Situation
    template_name = 'situations/situation_list.html'
    context_object_name = 'situations'

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Situation.objects.all()
        # Get situations with no roster restrictions
        queryset = Situation.objects.filter(roster_names=[])
        # Add situations where user's character is in an allowed roster
        character_rosters = RosterMember.objects.filter(
            character__account=user,
            approved=True
        ).values_list('roster__name', flat=True)
        roster_situations = Situation.objects.exclude(roster_names=[]).filter(
            roster_names__overlap=list(character_rosters)
        )
        return (queryset | roster_situations).distinct()

class SituationDetailView(LoginRequiredMixin, SituationAccessMixin, DetailView):
    """View a specific situation."""
    model = Situation
    template_name = 'situations/situation_detail.html'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.has_access(self.object):
            return HttpResponseForbidden("You don't have access to this situation.")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        situation = self.object
        context['details'] = [d for d in situation.details.all() 
                            if self.request.user.is_staff or not d.roster_names 
                            or any(name in d.roster_names for name in self.request.user.character.roster_names)]
        context['developments'] = [d for d in situation.developments.all()
                                 if self.request.user.is_staff or not d.roster_names
                                 or any(name in d.roster_names for name in self.request.user.character.roster_names)]
        return context

class SituationCreateView(StaffRequiredMixin, SituationFormMixin, CreateView):
    """Create a new situation."""
    model = Situation
    form_class = SituationForm
    template_name = 'situations/situation_form.html'
    success_url = reverse_lazy('situations:list')

class SituationUpdateView(StaffRequiredMixin, SituationFormMixin, UpdateView):
    """Update an existing situation."""
    model = Situation
    form_class = SituationForm
    template_name = 'situations/situation_form.html'

    def get_success_url(self):
        return reverse('situations:detail', kwargs={'pk': self.object.pk})

    def post(self, request, *args, **kwargs):
        # Handle job removal if requested
        if 'remove_job' in request.POST:
            self.object = self.get_object()
            job_id = request.POST.get('remove_job')
            try:
                job = Job.objects.get(id=job_id)
                self.object.related_jobs.remove(job)
                messages.success(request, f'Job #{job.id} "{job.title}" has been unlinked from this situation.')
            except Job.DoesNotExist:
                messages.error(request, f'Job #{job_id} not found.')
            return redirect('situations:edit', pk=self.object.pk)
        return super().post(request, *args, **kwargs)

class SituationDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a situation."""
    model = Situation
    template_name = 'situations/situation_confirm_delete.html'
    success_url = reverse_lazy('situation_list')

class DetailCreateView(StaffRequiredMixin, CreateView):
    """Create a new detail."""
    model = Detail
    form_class = DetailForm
    template_name = 'situations/detail_form.html'

    def form_valid(self, form):
        situation = get_object_or_404(Situation, pk=self.kwargs['situation_pk'])
        form.instance.situation = situation
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.kwargs['situation_pk']})

class DetailUpdateView(StaffRequiredMixin, UpdateView):
    """Update an existing detail."""
    model = Detail
    form_class = DetailForm
    template_name = 'situations/detail_form.html'

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.object.situation.pk})

class DetailDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a detail."""
    model = Detail
    template_name = 'situations/detail_confirm_delete.html'

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.object.situation.pk})

class DevelopmentCreateView(StaffRequiredMixin, CreateView):
    """Create a new development."""
    model = Development
    form_class = DevelopmentForm
    template_name = 'situations/development_form.html'

    def form_valid(self, form):
        situation = get_object_or_404(Situation, pk=self.kwargs['situation_pk'])
        form.instance.situation = situation
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.kwargs['situation_pk']})

class DevelopmentUpdateView(StaffRequiredMixin, UpdateView):
    """Update an existing development."""
    model = Development
    form_class = DevelopmentForm
    template_name = 'situations/development_form.html'

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.object.situation.pk})

class DevelopmentDeleteView(StaffRequiredMixin, DeleteView):
    """Delete a development."""
    model = Development
    template_name = 'situations/development_confirm_delete.html'

    def get_success_url(self):
        return reverse('situation_detail', kwargs={'pk': self.object.situation.pk}) 