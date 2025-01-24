# world/wod20th/views.py
from django.shortcuts import render, redirect
from .models import Stat
from .forms import StatForm

def stat_list(request):
    stats = Stat.objects.all()
    return render(request, 'stat_list.html', {'stats': stats})

def add_stat(request):
    if request.method == 'POST':
        form = StatForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('stat_list')
    else:
        form = StatForm()
    return render(request, 'add_stat.html', {'form': form})
