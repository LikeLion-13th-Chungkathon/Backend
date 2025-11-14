from django.urls import path
from .views import *

urlpatterns = [
    path('', ProjectCreateView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/house/', ProjectHouseView.as_view(), name="project-house"),
    path('<int:pk>/house/contribution/', ContributionView.as_view(), name="project-house-contribution"),

    path('invite/', InviteCodeView.as_view(), name='invite_code'),
    
    # path('<int:pk>/tagstyle/<int:tagstyle_id>/', TagStyleDeleteView.as_view(), name='tag_style-delete')
]