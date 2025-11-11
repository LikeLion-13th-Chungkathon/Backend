from django.shortcuts import render
from .models import Memo
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from .serializers import MemoSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema

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
            serializer.save(user=request.user)
            return Response({"results": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    # 로그인한 사용자의 메모 리스트 조회
    def get(self, request):
        user = request.user
        memos = Memo.objects.filter(user=user).order_by("-created_at")
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
