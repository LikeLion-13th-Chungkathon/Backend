from django.shortcuts import render
from .models import Memo
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from .serializers import MemoSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime
from portfolios.models import Log
from drf_yasg import openapi

class UserMemoListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=MemoSerializer,
        responses={201: "memo created"}
    )
    # 메모 작성
    def post(self, request):
        serializer = MemoSerializer(data=request.data)
        if serializer.is_valid():
            memo = serializer.save(user=request.user)
            log_result = Log.give_log(request.user, memo.project, "DAILY_COMPLETE")
            return Response(
                {
                    "results": serializer.data, 
                    "log_result": log_result
                }, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # 로그인한 사용자의 특정 프로젝트 메모 리스트를 날짜별로 조회
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="프로젝트 id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'date',
                openapi.IN_QUERY,
                description="날짜(YYYY-MM-DD)",
                type=openapi.TYPE_STRING,
            )
        ]
    )
    def get(self, request):
        user = request.user
        project_id = request.query_params.get("project_id")
        date = request.query_params.get("date")  # "2025-11-12"

        memos = Memo.objects.filter(user=user)

        # 프로젝트 기준 필터링
        if project_id:
            memos = memos.filter(project_id=project_id)

        # 날짜 기준 필터링
        if date:
            try:
                date = datetime.strptime(date, "%Y-%m-%d").date()
                memos = memos.filter(created_at__date=date)
            except ValueError:
                return Response({"error": "Invalid date format (YYYY-MM-DD expected)"}, status=status.HTTP_400_BAD_REQUEST)

        memos = memos.order_by("-created_at")
        serializer = MemoSerializer(memos, many=True, context={"request": request})
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

class UserMemoDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    # 메모 상세 조회
    def get(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MemoSerializer(memo)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        request_body=MemoSerializer,
        responses={201: "memo updated"}
    )
    # 메모 수정
    def put(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = MemoSerializer(memo, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"results": serializer.data}, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # 메모 삭제
    def delete(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        memo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
