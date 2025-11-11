from django.urls import path
from .views import *

urlpatterns = [
    path('', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/tag/', TagStyleCreateView.as_view(), name='tag_style-create'),
    
    path('tag/<int:tagstyle_id>/', TagStyleDeleteView.as_view(), name='tag_style-create')
]