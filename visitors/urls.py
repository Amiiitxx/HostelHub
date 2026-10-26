from django.urls import path
from . import views

app_name = 'visitors'

urlpatterns = [

    path(
        '',
        views.visitor_list,
        name='list'
    ),

    path(
        'apply/',
        views.visitor_apply,
        name='apply'
    ),

    path(
        'checkin/',
        views.visitor_create,
        name='create'
    ),

    path(
        '<int:pk>/approve/',
        views.visitor_approve,
        name='approve'
    ),

    path(
        '<int:pk>/reject/',
        views.visitor_reject,
        name='reject'
    ),

    path(
        '<int:pk>/check-in/',
        views.visitor_checkin,
        name='checkin'
    ),

    path(
        '<int:pk>/checkout/',
        views.visitor_checkout,
        name='checkout'
    ),
]