from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('situations/', include('world.situations.urls', namespace='situations')),
] 