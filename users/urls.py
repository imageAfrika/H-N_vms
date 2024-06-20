from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # clients list
    path('clients/', views.client_list, name='client_list'),

    #client details
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),

    # register client
    path('register/', views.register_client, name='register_client'),

    # user visit
    path('visit/<int:client_id>/', views.visit, name='visit'),

    # redeem visit points
    path('redeem_points/<int:client_id>/', views.redeem_points, name='redeem_points'),

    # redeem referral points
    path('redeem_referral_points/<int:client_id>/', views.redeem_referral_points, name='redeem_referral_points'),
]