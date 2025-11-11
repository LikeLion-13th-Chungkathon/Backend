from django.contrib import admin
from django.urls import path, include

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger 설정
schema_view = get_schema_view(
    openapi.Info(
        title="중앙대학교 멋쟁이 사자처럼 13기 중커톤 프로젝트 API",
        default_version="v1",
        description="해커톤 프로젝트 API 문서입니다.",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('accounts.urls')),
    path('projects/', include('portfolios.urls')),
    path('memos/', include('memos.urls')),
    path('taggings/', include('taggings.urls')),
    
    # Swagger UI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
