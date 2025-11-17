from rest_framework_simplejwt.serializers import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout

from config.settings import get_secret
from django.shortcuts import redirect
from json import JSONDecodeError
from django.http import JsonResponse
import requests 
import json

# -- JWT 기반 회원가입 뷰 --
class RegisterView(APIView):
    @swagger_auto_schema(
        operation_summary= "JWT 기반 회원가입 (지금 프로젝트에선 사용 안 함)",
        operation_description= "Oauth를 사용하고 있기에 지금은 사용하지 않음. 사용할 것을 대비하여 남겨둠.",
        request_body=RegisterSerializer,
        responses={201: "register success"}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        # 유효성 검사 
        if serializer.is_valid(raise_exception=True):
            
            # 유효성 검사 통과 후 객체 생성
            user = serializer.save()

            # user에게 refresh token 발급
            token = RefreshToken.for_user(user)
            refresh_token = str(token)
            access_token = str(token.access_token)

            res = Response(
                {
                    "user": serializer.data,
                    "message": "register success!",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }, 
                },
                status=status.HTTP_201_CREATED,
            )
            return res
        

class AuthView(APIView):
    @swagger_auto_schema(
        operation_summary= "JWT 기반 로그인 (지금 프로젝트에선 사용 안 함)",
        operation_description= "Oauth를 사용하고 있기에 지금은 사용하지 않음. 사용할 것을 대비하여 남겨둠.",
        request_body=AuthSerializer,
        responses={200: "login success"}
    )
    def post(self, request):
        serializer = AuthSerializer(data=request.data)
        
        # 유효성 검사
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            access_token = serializer.validated_data['access_token']
            refresh_token = serializer.validated_data['refresh_token']

            res = Response(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                    },
                    "message": "login success!",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    }, 
                },
                status=status.HTTP_200_OK,
            )

            res.set_cookie("access_token", access_token, httponly=True)
            res.set_cookie("refresh_token", refresh_token, httponly=True)
            return res
        
        # 유효성 검사 실패 시 오류 반환
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: "logout success"}
    )
    def post(self, request):
        logout(request)
        return Response({"message": "logout success!"}, status=status.HTTP_200_OK)
    

# -- Oauth2 기반 회원가입/로그인 뷰 --

# 구글 소셜 로그인 용 설정
#GOOGLE_REDIRECT = get_secret("GOOGLE_REDIRECT")
GOOGLE_CALLBACK_URI = get_secret("GOOGLE_CALLBACK_URI") # 프론트의 주소도 추가 되어 있어야 함.
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_SECRET = get_secret("GOOGLE_SECRET")
GOOGLE_SCOPE = get_secret("GOOGLE_SCOPE_USERINFO")

# 프론트와 협업 시, google_login 뷰는 프론트에서 구현하므로 삭제 예정
# def google_login(request):
#     return redirect(f"{GOOGLE_REDIRECT}?client_id={GOOGLE_CLIENT_ID}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={GOOGLE_SCOPE}")


@swagger_auto_schema(
    method="post",
    operation_summary="구글 소셜 로그인 콜백",
    operation_description=(
        "프론트엔드에서 전달한 Google OAuth 인가코드(code)를 사용해 "
        "구글 access token 및 사용자 정보를 받아온 뒤,\n"
        "이미 가입된 유저면 바로 로그인 처리, 비회원이면 닉네임 입력을 요청하는 API입니다.\n\n"
        "요청 예시:\n"
        "{\n"
        '  "code": "4/0AfJohX..."\n'
        "}\n\n"
        "응답 분기:\n"
        "- 200 OK: 기존 회원 → 토큰 발급 및 로그인 완료\n"
        "- 202 Accepted: 신규 회원 → 닉네임 입력 필요 (signup API 호출해야 함)"
    ),
    tags=["Oauth"],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["code"],
        properties={
            "code": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Google OAuth 인가코드",
                example="4/0AfJohXabcdEFG...",
            ),
        },
    ),
    responses={
        200: openapi.Response(
            description="기존 회원, 로그인 성공",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "user": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "id": openapi.Schema(
                                type=openapi.TYPE_INTEGER,
                                example=1,
                            ),
                            "username": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="myNickname",
                            ),
                            "email": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="user@gmail.com",
                            ),
                            "nickname": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                example="myNickname",
                            ),
                        },
                    ),
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="google social login success!",
                    ),
                    "token": openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "access_token": openapi.Schema(
                                type=openapi.TYPE_STRING
                            ),
                            "refresh_token": openapi.Schema(
                                type=openapi.TYPE_STRING
                            ),
                        },
                    ),
                },
            ),
        ),
        202: openapi.Response(
            description="신규 회원, 닉네임 입력 필요",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "message": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="new_user_nickname_required",
                    ),
                    "email": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="user@gmail.com",
                    ),
                    "username_from_google": openapi.Schema(
                        type=openapi.TYPE_STRING,
                        example="John Doe",
                        description="구글에서 넘어온 name 값",
                    ),
                },
            ),
        ),
        400: openapi.Response(
            description="code 누락 또는 Google/Token 오류",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                example={"error": "Authorization code error."},
            ),
        ),
    },
)
@api_view(["POST"])
def google_callback(request):
    
    
    # 프론트 협업 시 추가(프론트가 body로 인가코드를 넘겨준다고 가정)
    body = json.loads(request.body.decode('utf-8'))
    code = body['code'] # 프론트가 어떻게 넘겨주냐에 따라 달라짐

    # 인가코드 받아오기 (프론트 협업시 삭제 예정)
    # code = request.GET.get("code", None)     
    
    if code is None:
        return JsonResponse({'error': 'Authorization code error.'}, status=status.HTTP_400_BAD_REQUEST)

    # 인가코드로 access token 받기
    token_req = requests.post(f"https://oauth2.googleapis.com/token?client_id={GOOGLE_CLIENT_ID}&client_secret={GOOGLE_SECRET}&code={code}&grant_type=authorization_code&redirect_uri={GOOGLE_CALLBACK_URI}")
    token_req_json = token_req.json()
    error = token_req_json.get("error")

    if error is not None:
        raise JSONDecodeError(error)

    google_access_token = token_req_json.get('access_token')

    # access token으로 구글 계정 정보 가져오기
    user_info = requests.get(f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={google_access_token}")
    res_status = user_info.status_code

    if res_status != 200:
        return JsonResponse({'status': 400,'message': 'Failed to get access token'}, status=status.HTTP_400_BAD_REQUEST)
    
    user_info_json = user_info.json()

    email = user_info_json.get('email')
    username_from_google = user_info_json.get('name') # 유저가 언급한 "랜덤 문자열"(실제로는 Google 이름)

    if not email:
        return JsonResponse({'error': 'Email not provided by Google.'}, status=status.HTTP_400_BAD_REQUEST)

    # --- 로직 변경 지점 ---
    # 기존 OAuthSerializer 대신 뷰에서 직접 유저 존재 여부 확인
    
    user = User.get_user_by_email(email=email)

    if user:
        # --- CASE 1: 사용자가 존재할 경우 (로그인) ---
        # 기존 사용자이므로, 토큰을 발급하여 로그인시킵니다.
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        refresh_token = str(token)

        res = JsonResponse(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "nickname": user.nickname, # 닉네임 정보 추가
                },
                "message": "google social login success!",
                "token": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            },
            status=status.HTTP_200_OK,
        )
        res.set_cookie("access-token", access_token, httponly=True)
        res.set_cookie("refresh-token", refresh_token, httponly=True)
        return res
    
    else:
        # --- CASE 2: 사용자가 존재하지 않을 경우 (신규 가입) ---
        # 신규 사용자이므로, 프론트엔드에 닉네임 입력을 요청합니다.
        # Google이 제공한 이메일과 이름을 반환하여 프론트가 다음 단계(회원가입)에서 사용하도록 합니다.
        return JsonResponse(
            {
                "message": "new_user_nickname_required",
                "email": email,
                "username_from_google": username_from_google,
            },
            status=status.HTTP_202_ACCEPTED # 202 Accepted: 요청은 받았으나 처리가 완료되지 않음 (닉네임 필요)
        )

class GoogleSignupView(APIView):
    """
    프론트엔드에서 닉네임까지 모두 받아 실제 회원가입을 처리합니다.
    (POST: /accounts/google/signup/ 등)
    """
    @swagger_auto_schema(
        operation_summary="구글 소셜 회원가입 완료 (닉네임 설정)",
        operation_description=(
            "비회원인 경우 callback 이후 조건부로 접근하는 엔드포인트입니다.\n\n"
            "프론트엔드에서 전달받은 구글 이메일과 닉네임을 이용해 "
            "User를 생성하고 JWT 토큰(access/refresh)을 발급합니다.\n\n"
            "요청 예시:\n"
            "{\n"
            '   "email": "google_email@gmail.com",\n'
            '   "username_from_google": "raw google username",\n'
            '   "nickname": "사용자가 선택한 닉네임"\n'
            "}"
        ),
        tags=["Oauth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "nickname"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="google_email@gmail.com",
                ),
                "username_from_google": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="John Doe",
                    description="구글 프로필에서 받아온 name 값. 서버는 닉네임으로 사용하지 않음.",
                ),
                "nickname": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="myCustomNickname",
                    description="사용자가 실제로 사용할 닉네임",
                ),
            },
        ),
        responses={
            201: openapi.Response(
                description="google social signup success!",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(
                                    type=openapi.TYPE_INTEGER,
                                    example=1,
                                ),
                                "username": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="myCustomNickname",
                                    description="닉네임(=username)",
                                ),
                                "email": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="google_email@gmail.com",
                                ),
                                "nickname": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="myCustomNickname",
                                ),
                            },
                        ),
                        "message": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            example="google social signup success!",
                        ),
                        "token": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "access_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                ),
                                "refresh_token": openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...(refresh)",
                                ),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description="잘못된 요청 또는 Validation Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    example={"error": "invalid data"},
                ),
            ),
        },
    )
    def post(self, request):
        # 프론트엔드는 202 응답을 받고, 사용자가 닉네임을 입력하면
        # { email, username_from_google, nickname }을 이 API로 전송합니다.
        
        serializer = GoogleSignupSerializer(data=request.data)
        
        if serializer.is_valid(raise_exception=True):
            # 시리얼라이저의 create_user_and_get_tokens 메서드 호출
            data = serializer.save() 
            
            user = data['user']
            access_token = data['access_token']
            refresh_token = data['refresh_token']

            res = JsonResponse(
                {
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "nickname": user.nickname,
                    },
                    "message": "google social signup success!",
                    "token": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                    },
                },
                status=status.HTTP_201_CREATED, # 201 Created: 리소스 생성 성공
            )
            res.set_cookie("access-token", access_token, httponly=True)
            res.set_cookie("refresh-token", refresh_token, httponly=True)
            return res
        
        # raise_exception=True로 인해 유효성 검사 실패 시 400 Bad Request 자동 반환

# # -- TeamMember 관련 뷰 --
# class TeamMemberCreateView(APIView):
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(
#         request_body=TeamMemberSerializer,
#         responses={201: "team member created"}
#     )
#     def post(self, request):
#         serializer = TeamMemberSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         try:
#             team_member = serializer.save()
#         except ValidationError as e:
#             # 모델에서 발생한 ValidationError를 400으로 반환
#             return Response(
#                 {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
#             )
        
#         return Response(TeamMemberSerializer(team_member).data, status=status.HTTP_201_CREATED)

class UserView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="내 정보 조회",
        operation_description="현재 로그인된 사용자의 정보를 반환합니다.",
        responses={
            200: openapi.Response(
                description="성공적으로 사용자 정보를 반환",
                schema=UserSerializer()
            ),
            401: "인증 실패(로그인 필요)"
        }
    )
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)


class TeamMemberListView(APIView):
    permission_classes = [IsAuthenticated]
   
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description="프로젝트 id",
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                'role',
                openapi.IN_QUERY,
                description="역할(Member, Admin)",
                type=openapi.TYPE_STRING,
            )
        ],
        responses={
            200: openapi.Response(
                description="팀 멤버 리스트 조회 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "results": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "user": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        example=3
                                    ),
                                    "project": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        example=12
                                    ),
                                    "role": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        example="Member"
                                    ),
                                    "joined_at": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        example="2025-11-14T23:50:00.123456+09:00"
                                    )
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    def get(self, request):
        team_members = TeamMember.objects.all()

        project_id = request.query_params.get("project_id")
        role = request.query_params.get("role")

        if project_id:
            team_members = team_members.filter(project__id=project_id)

        if role:
            team_members = team_members.filter(role=role)

        serializer = TeamMemberSerializer(team_members, many=True)
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)