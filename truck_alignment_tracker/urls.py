from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('service/', include('service_tracking.urls')),
    path('', include('alignments.urls')),
]
