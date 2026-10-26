from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [

    path('login/', views.login_view, name='login'),

    path('signup/', views.signup_view, name='signup'),

    path('logout/', views.logout_view, name='logout'),

    path('profile/', views.profile_view, name='profile'),

    path('users/', views.user_list_view, name='user_list'),

    path('users/create/', views.user_create_view, name='user_create'),

]