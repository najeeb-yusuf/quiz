from django.urls import path, include
from . import views 

urlpatterns = [
    path('', views.language, name='lang'),
    path('home/', views.index, name='index'),
    path('mail/', views.enter_mail, name='mail'),
    path('results/', views.results, name='results'),
    path('send_mail/', views.send_email, name='send_mail'),
    path('responses/', views.responses, name='responses'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_user, name='logout'),
]