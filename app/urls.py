from django.urls import path
from app import views


urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('chat/<str:group_name>/', views.Chatting, name='chatting'),
]

