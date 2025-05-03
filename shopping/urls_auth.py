from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserRegistrationView.as_view(), name='register'),
]