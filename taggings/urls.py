from django.urls import path
from .views import *

urlpatterns = [
    path('<int:tagging_id>/', TaggingDetailView.as_view()),
    path('project/<int:project_id>/', ProjectTaggingView.as_view()),
    path('memo/<int:memo_id>/', MemoTaggingView.as_view())
]
