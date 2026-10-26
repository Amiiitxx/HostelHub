from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('create/', views.fee_create, name='create'),
    path('<int:pk>/', views.fee_detail, name='detail'),
    path('<int:pk>/delete/', views.fee_delete, name='delete'),
    path('<int:fee_pk>/payment/', views.payment_create, name='payment_create'),
    path('receipt/<int:pk>/', views.receipt_view, name='receipt'),
]
