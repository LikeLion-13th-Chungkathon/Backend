from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import Project
from rest_framework import status

from rest_framework.permissions import IsAuthenticated, BasePermission
from django.http import Http404

class IsProjectOwner(BasePermission):
    """
    요청을 보낸 유저가 해당 프로젝트의 'owner'인지 확인합니다.
    """
    def has_object_permission(self, request, view, obj):
        # obj는 'get_object' 메서드에서 반환된 Project 인스턴스입니다.
        return obj.owner == request.user

class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        if serializer.is_valid():
            # serializer.save()가 호출될 때,
            # 'owner'를 request.user로 지정하여 넘겨줍니다.
            # 이 'owner' 값은 serializer의 create 메서드로 전달됩니다.
            serializer.save(owner=request.user) 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# 조회, 수정, 삭제를 위한 뷰
class ProjectDetailView(APIView):
    # 1. 인증된 사용자인지 확인
    # 2. 해당 프로젝트의 소유자인지 확인 (IsProjectOwner)
    permission_classes = [IsAuthenticated, IsProjectOwner]

    def get_object(self, pk):
        """
        pk에 해당하는 Project 객체를 가져오고, 권한 검사를 수행합니다.
        """

        try:
            project = Project.objects.get(pk=pk)
            # has_object_permission (IsProjectOwner) 권한 검사 실행
            self.check_object_permissions(self.request, project)
            return project
        except Project.DoesNotExist:
            raise Http404

    # --- 상세 조회 (GET) ---
    def get(self, request, pk):
        project = self.get_object(pk)
        serializer = ProjectSerializer(project) # 조회용 Serializer 사용
        return Response(serializer.data)

    # --- 수정 (PUT: 전체 수정) ---
    def put(self, request, pk):
        project = self.get_object(pk)
        # 수정 시에는 ProjectSerializer 사용
        serializer = ProjectSerializer(project, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # --- 수정 (PATCH: 부분 수정) ---
    def patch(self, request, pk):
        project = self.get_object(pk)
        # partial=True 옵션으로 부분 수정 허용
        serializer = ProjectSerializer(project, data=request.data, partial=True) 
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # --- 삭제 (DELETE) ---
    def delete(self, request, pk):
        project = self.get_object(pk)
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)