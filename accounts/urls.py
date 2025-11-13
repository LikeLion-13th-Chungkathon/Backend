from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("join/", RegisterView.as_view()),
    path("login/", AuthView.as_view()),
    path("logout/", LogoutView.as_view()),

    # 소셜로그인
    path("google/login/", google_login, name="google_login"), # 프론트 협업 시 삭제
    path("google/callback/", google_callback, name="google_callback"),
    path('google/signup/', GoogleSignupView.as_view(), name='google_signup'),

    # path("team/members/", TeamMemberCreateView.as_view()),
    path("team/members/list/", TeamMemberListView.as_view()),

    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
]