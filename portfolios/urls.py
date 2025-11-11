from django.urls import path
from .views import *

urlpatterns = [
    path('projects/', ProjectCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
]