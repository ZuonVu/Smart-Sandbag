from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views 
from sandbag_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- Auth URLs ---
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),  # New registration URL
    
    # --- App URLs ---
    path('', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
    path('export/<int:session_id>/', views.export_session_csv, name='export_csv'),
    path('record/', views.record_punch, name='record_punch'),
    path('start_session/', views.start_session, name='start_session'),
    path('end_session/', views.end_session, name='end_session'),
    path('settings/', views.settings, name='settings'),
    path('delete_session/<int:session_id>/', views.delete_session, name='delete_session'),
]