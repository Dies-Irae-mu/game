from django.contrib import admin
from world.plots.models import Plot, Session

class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    fields = ['id', 'date', 'duration', 'location', 'event_id']
    readonly_fields = ['id']

@admin.register(Plot)
class PlotAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'genre', 'risk_level', 'claimed', 'storyteller']
    list_filter = ['status', 'genre', 'risk_level', 'claimed']
    search_fields = ['title', 'description']
    inlines = [SessionInline]

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'plot', 'date', 'duration', 'location', 'event_id']
    list_filter = ['plot__title', 'date']
    search_fields = ['description', 'location', 'plot__title']
    raw_id_fields = ['plot']
