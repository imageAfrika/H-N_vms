from django.urls import path, include
from users import views

app_name = 'services'

urlpatterns = [
    # all services
    path('all/', views.service_list, name='service_list'),

    # add service
    path('add/', views.add_service, name='add_service'),

    # edit service
    path('edit/<int:service_id>/', views.edit_service, name='edit_service'),

    # delete srvice
    path('delete/<int:service_id>/', views.delete_service, name='delete_service'),

    # create order
    path('order/create/<int:client_id>/', views.create_order, name='create_order'),

    # edit order
    path('order/edit/<int:order_id>/', views.edit_order, name='edit_order'),

    # delete order
    path('order/delete_item/<int:order_id>/<int:item_id>/', views.delete_order_item, name='delete_order_item'),

    # process payment
    path('order/proceed_to_payment/<int:order_id>/', views.proceed_to_payment, name='proceed_to_payment'),

    # each order
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),

    # payments
    path('payments/summary/', views.daily_payments_summary, name='daily_payments_summary'),

]