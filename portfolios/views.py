from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from .models import Project, TagStyle
from accounts.models import TeamMember
from accounts.serializers import TeamMemberSerializer
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema

class IsProjectOwner(BasePermission):
    """
    요청을 보낸 유저가 해당 프로젝트의 'owner'인지 확인합니다.
    """
    def has_object_permission(self, request, view, obj):
        # obj는 'get_object' 메서드에서 반환된 Project 인스턴스입니다.
        return obj.owner == request.user

class ProjectCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ProjectCreateSerializer,
        responses={201: "project created"}
    )
    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # serializer.save()가 호출될 때,
            # 'owner'를 request.user로 지정하여 넘겨줍니다.
            # 이 'owner' 값은 serializer의 create 메서드로 전달됩니다.
            project = serializer.save(owner=request.user)

            # 생성한 사람 Admin으로 설정
            TeamMember.objects.create(
                user=request.user,
                project=project,
                role="Admin"
            )

            # 프로젝트의 통나무집 기본값으로 생성
            ProjectHouse.objects.create(
                project=project,
                difficulty_ratio=0.85, 
                total_required_logs=0,   
                current_logs=0
            )
        except ValidationError as e:
            # 모델에서 발생한 clean() 예외 처리 (프로젝트 6명 인원 제한)
            return Response(
                {"error": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # 모든 프로젝트 리스트 조회
    def get(self, request):
        projects = Project.objects.all().order_by("-created_at")
        serializer = ProjectSerializer(projects, many=True, context={"request": request})
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)
    
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
    @swagger_auto_schema(
        request_body=ProjectSerializer,
        responses={200: "project all updated"}
    )
    def put(self, request, pk):
        project = self.get_object(pk)
        # 수정 시에는 ProjectSerializer 사용
        serializer = ProjectSerializer(project, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # --- 수정 (PATCH: 부분 수정) ---
    @swagger_auto_schema(
        request_body=ProjectSerializer,
        responses={200: "project part updated"}
    )
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
    
class TagStyleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    # 태그 스타일 생성
    @swagger_auto_schema(
        request_body=TagStyleSerializer,
        responses={201: "tag created"}
    )
    def post(self, request, pk):
        project = get_object_or_404(Project, id=pk)

        if project.owner != request.user:
            return Response({"detail": "팀장만 태그 스타일을 생성할 수 있습니다."},
                            status=status.HTTP_403_FORBIDDEN)
    
        serializer = TagStyleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            return Response({"results": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class TagStyleDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    # 태그 스타일 삭제
    def delete(self, request, pk, tagstyle_id):
        project = get_object_or_404(Project, id=pk)

        if project.owner != request.user:
            return Response({"detail": "팀장만 태그 스타일을 삭제할 수 있습니다."},
                            status=status.HTTP_403_FORBIDDEN)
    
        tag_style = get_object_or_404(TagStyle, id=tagstyle_id, project=project)
        tag_style.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class InviteCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get("invite_code")
        project = get_object_or_404(Project, invite_code=invite_code)
        user = request.user

        # 이미 해당 프로젝트에 가입되어 있는지 확인
        if TeamMember.objects.filter(user=user, project=project).exists():
            return Response(
                {"message": "이미 해당 프로젝트에 속해있습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 실제 가입 시도
        try:
            team_member = TeamMember.objects.create(
                user=user,
                project=project,
                role="Member"
            )
        except ValidationError as e:
            # 모델에서 발생한 clean() 예외 처리 (프로젝트 6명 인원 제한)
            return Response(
                {"error": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            {
                "message": f"'{project.project_name}' 프로젝트에 성공적으로 가입했습니다!",
                "team_member": TeamMemberSerializer(team_member).data
            },
            status=status.HTTP_201_CREATED
        )
    
class ProjectHouseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        house = get_object_or_404(ProjectHouse, project=project)

        # 진행률 업데이트
        house.current_logs = Log.objects.filter(project=project).count()
        house.total_required_logs = house.calculate_required_logs()
        house.save()

        serializer = ProjectHouseSerializer(house)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ContributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        project = get_object_or_404(Project, id=pk)
        team_members = TeamMember.objects.filter(project=project)
        serializer = ContributionSerializer(team_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
