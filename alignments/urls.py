from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_alignment, name='add_alignment'),
    path('edit/<int:pk>/', views.edit_alignment, name='edit_alignment'),
    path('delete/<int:pk>/', views.delete_alignment, name='delete_alignment'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/csv/', views.export_csv, name='export_csv'),
    path('reports/export/excel/', views.export_excel, name='export_excel'),
    path('reports/export/pdf/', views.export_pdf, name='export_pdf'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='alignments/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # User management (staff only)
    path('users/', views.user_management, name='user_management'),
]
