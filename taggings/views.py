from django.shortcuts import render
from portfolios.models import Project
from memos.models import Memo
from .models import Tagging
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from .serializers import TaggingSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

# 한 메모에 대한 태깅
class MemoTaggingView(APIView):
    permission_classes = [IsAuthenticated]

    # 메모에 태깅 추가
    @swagger_auto_schema(
        request_body=TaggingSerializer,
        responses={201: "tagging created"}
    )
    def post(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TaggingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(memo=memo, user=request.user)
            return Response({"results": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # 한 메모의 태깅 리스트
    def get(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        taggings = Tagging.objects.filter(memo=memo).order_by("created_at")
        serializer = TaggingSerializer(taggings, many=True, context={"request": request})
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

class ProjectTaggingView(APIView):
    permission_classes = [IsAuthenticated]

    # 로그인한 사용자의 한 프로젝트 태깅 리스트 조회
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        taggings = (
            Tagging.objects
            .filter(user=request.user, memo__project=project)
            .select_related("tag_style", "memo")
            .order_by("created_at")
        )

        # tag_style 기준으로 그룹핑
        grouped = defaultdict(list)
        for tagging in taggings:
            grouped[tagging.tag_style].append(tagging)

        categories = []
        for tag_style, tagging_list in grouped.items():
            tag_style_data = {
                "id": tag_style.id,
                "tag_detail": tag_style.tag_detail,
                "tag_color": tag_style.tag_color,
            }
            serializer = TaggingSerializer(tagging_list, many=True, context={"request": request})
            categories.append({
                "tag_style": tag_style_data,
                "taggings": serializer.data
            })

        serializer = TaggingSerializer(taggings, many=True, context={"request": request})
        
        return Response({
            "project_id": project.id,
            "project_name": project.project_name,
            "categories": categories
        }, status=status.HTTP_200_OK)

class TaggingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # 태깅 상세 조회
    def get(self, request, tagging_id):
        tagging = get_object_or_404(Tagging, id=tagging_id)
        if request.user != tagging.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TaggingSerializer(tagging)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

    # 태깅 수정
    def put(self, request, tagging_id):
        tagging = get_object_or_404(Tagging, id=tagging_id)
        if request.user != tagging.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TaggingSerializer(tagging, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # 태깅 삭제
    def delete(self, request, tagging_id):
        tagging = get_object_or_404(Tagging, id=tagging_id)
        if request.user != tagging.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        tagging.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)