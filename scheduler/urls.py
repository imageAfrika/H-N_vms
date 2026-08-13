from django.urls import path
from . import views

app_name = 'scheduler'

urlpatterns = [
    # Calendar views
    path('', views.calendar_view, name='calendar'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', views.calendar_view, name='calendar_month'),
    
    # Appointment CRUD
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/edit/', views.appointment_update, name='appointment_update'),
    path('appointments/<int:pk>/delete/', views.appointment_delete, name='appointment_delete'),
    path('appointments/<int:pk>/confirm/', views.appointment_confirm, name='appointment_confirm'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    
    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/send/', views.message_send, name='message_send'),
    
    # Reminders
    path('reminders/', views.reminder_list, name='reminder_list'),
    path('reminders/create/', views.reminder_create, name='reminder_create'),
    
    # CalDAV / iCalendar
    path('ical/', views.ical_feed, name='ical_feed'),
    path('ical/<int:appointment_id>/', views.appointment_ical, name='appointment_ical'),
    
    # Dashboard
    path('dashboard/', views.scheduler_dashboard, name='dashboard'),
]