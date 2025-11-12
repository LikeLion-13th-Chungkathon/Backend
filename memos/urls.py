from django.urls import path
from .views import *

urlpatterns = [
    path('', UserMemoListView.as_view()),
    path('<int:memo_id>/', UserMemoDetailView.as_view()),
]