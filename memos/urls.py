from django.urls import path
from .views import *

urlpatterns = [
    path('memos/', UserMemoListView.as_view()),
    path('memos/<int:memo_id>/', UserMemoDetailView.as_view()),
]