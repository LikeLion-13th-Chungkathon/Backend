from django.shortcuts import render
from portfolios.models import Project
from memos.models import Memo
from .models import Tagging, TagStyle
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404 
from .serializers import TaggingSerializer, TagStyleSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from django.core.exceptions import ValidationError
from collections import defaultdict
from portfolios.models import Log
from drf_yasg import openapi

tagging_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
        "created_at": openapi.Schema(type=openapi.TYPE_STRING, example="2025-11-15T01:23:45.123456+09:00"),
        "modified_at": openapi.Schema(type=openapi.TYPE_STRING, example="2025-11-15T01:23:45.123456+09:00"),
        "tag_contents": openapi.Schema(type=openapi.TYPE_STRING, example="중요"),
        "offset_start": openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
        "offset_end": openapi.Schema(type=openapi.TYPE_INTEGER, example=12),
        "tag_style": openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
        "user": openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
        "memo": openapi.Schema(type=openapi.TYPE_INTEGER, example=7),
    }
)


# 한 메모에 대한 태깅
class MemoTaggingView(APIView):
    permission_classes = [IsAuthenticated]

    # 메모에 태깅 추가
    @swagger_auto_schema(
        request_body=TaggingSerializer,
        responses={
            201: openapi.Response(
                description="태깅 생성 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": tagging_schema,
                        "log_result": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                                "message": openapi.Schema(type=openapi.TYPE_STRING, example="통나무 지급 성공 (TAG_REVIEW_COMPLETE)")
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="offset_start는 offset_end보다 클 수 없습니다."
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Permission denied"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="메모를 찾을 수 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def post(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TaggingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            serializer.save(memo=memo, user=request.user)
            log_result = Log.give_log(request.user, memo.project, "TAG_REVIEW_COMPLETE")
       
        except ValidationError as e:
            # 모델에서 발생한 clean() 예외 처리 (프로젝트 6명 인원 제한)
            return Response(
                {"error": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "results": serializer.data,
                "log_result": log_result,
            },
            status=status.HTTP_201_CREATED,
        )
    
    # 한 메모의 태깅 리스트
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="태깅 리스트 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=tagging_schema
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Permission denied"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="메모 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def get(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)
        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        taggings = Tagging.objects.filter(memo=memo).order_by("-created_at")
        serializer = TaggingSerializer(taggings, many=True, context={"request": request})
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="메모의 모든 태깅 삭제",
        operation_description="""
    해당 메모에 달린 모든 태깅(Tagging)을 삭제합니다.  
    - 로그인한 사용자 본인의 메모만 삭제할 수 있습니다.
    - 삭제 후에는 204 No Content 를 반환합니다.
        """,
        responses={
            204: openapi.Response(
                description="모든 태깅 삭제 성공",
                examples={
                    "application/json": {
                        "message": "메모의 모든 태깅이 삭제되었습니다."
                    }
                }
            ),
            403: openapi.Response(
                description="메모 주인이 아닌 경우",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "Permission denied"
                    }
                }
            ),
            404: openapi.Response(
                description="메모를 찾을 수 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING)
                    }
                ),
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            ),
        }
    )
    def delete(self, request, memo_id):
        memo = get_object_or_404(Memo, id=memo_id)

        if request.user != memo.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        Tagging.objects.filter(memo=memo).delete()

        return Response(
            {"message": "해당 메모의 모든 태깅이 삭제되었습니다."},
            status=status.HTTP_204_NO_CONTENT
        )


tag_style_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=0),
        "tag_detail": openapi.Schema(type=openapi.TYPE_STRING, example="문제"),
        "tag_color": openapi.Schema(type=openapi.TYPE_STRING, example="#FFEC5E"),
    }
)

class ProjectTaggingView(APIView):
    permission_classes = [IsAuthenticated]

    # 로그인한 사용자의 한 프로젝트 태깅 리스트 조회
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="로그인한 사용자의 프로젝트별 태깅 카테고리 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "project_id": openapi.Schema(type=openapi.TYPE_INTEGER, example=7),
                        "project_name": openapi.Schema(type=openapi.TYPE_STRING, example="내 프로젝트"),
                        "categories": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "tag_style": tag_style_schema,
                                    "taggings": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=tagging_schema
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Permission denied")
                    }
                )
            ),
            404: openapi.Response(
                description="프로젝트 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            ),
        }
    )
    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        taggings = (
            Tagging.objects
            .filter(user=request.user, memo__project=project)
            .select_related("tag_style", "memo")
            .order_by("-created_at")
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
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="태깅 상세 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": tagging_schema
                    }
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Permission denied"
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="태깅을 찾을 수 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="Not found."
                        )
                    }
                )
            )
        }
    )
    def get(self, request, tagging_id):
        tagging = get_object_or_404(Tagging, id=tagging_id)
        if request.user != tagging.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        serializer = TaggingSerializer(tagging)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

    # 태깅 수정
    @swagger_auto_schema(
        request_body=TaggingSerializer,
        responses={
            200: openapi.Response(
                description="태깅 수정 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": tagging_schema
                    }
                )
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    example={"tag_contents": ["이 필드는 필수 항목입니다."]}
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Permission denied")
                    }
                )
            ),
            404: openapi.Response(
                description="태깅 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
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
    @swagger_auto_schema(
        responses={
            204: openapi.Response(description="태깅 삭제 성공"),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Permission denied")
                    }
                )
            ),
            404: openapi.Response(
                description="태깅 없음",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "detail": openapi.Schema(type=openapi.TYPE_STRING, example="Not found.")
                    }
                )
            )
        }
    )
    def delete(self, request, tagging_id):
        tagging = get_object_or_404(Tagging, id=tagging_id)
        if request.user != tagging.user:
            return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        tagging.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    tag_style_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "id": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
        "project": openapi.Schema(type=openapi.TYPE_INTEGER, example=7),
        "tag_detail": openapi.Schema(type=openapi.TYPE_STRING, example="중요"),
        "tag_color": openapi.Schema(type=openapi.TYPE_STRING, example="#FFAA22"),
    }
)

class TagStyleView(APIView):
    permission_classes = [IsAuthenticated]

    # 태그 스타일 전체 리스트 조회
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="태그 스타일 리스트 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=tag_style_schema
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        tag_styles = TagStyle.objects.all()
        serializers = TagStyleSerializer(tag_styles, many=True, context={"request": request})
        return Response({"results": serializers.data}, status=status.HTTP_200_OK)