from rest_framework_simplejwt.serializers import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import logout

from rest_framework import status

from config.settings import get_secret
from django.shortcuts import redirect
from json import JSONDecodeError
from django.http import JsonResponse
import requests 


# -- JWT 기반 회원가입 뷰 --
class RegisterView(APIView):
    @swagger_auto_schema(
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
GOOGLE_REDIRECT = get_secret("GOOGLE_REDIRECT")
GOOGLE_CALLBACK_URI = get_secret("GOOGLE_CALLBACK_URI") # 프론트의 주소도 추가 되어 있어야 함.
GOOGLE_CLIENT_ID = get_secret("GOOGLE_CLIENT_ID")
GOOGLE_SECRET = get_secret("GOOGLE_SECRET")
GOOGLE_SCOPE = get_secret("GOOGLE_SCOPE")

# 프론트와 협업 시, google_login 뷰는 프론트에서 구현하므로 삭제 예정
def google_login(request):
    return redirect(f"{GOOGLE_REDIRECT}?client_id={GOOGLE_CLIENT_ID}&response_type=code&redirect_uri={GOOGLE_CALLBACK_URI}&scope={GOOGLE_SCOPE}")

def google_callback(request):
    
    
    # 프론트 협업 시 추가(프론트가 body로 인가코드를 넘겨준다고 가정)
    # body = json.loads(request.body.decode('utf-8'))
    # code = body['code'] # 프론트가 어떻게 넘겨주냐에 따라 달라짐

    # 인가코드 받아오기 (프론트 협업시 삭제 예정)
    code = request.GET.get("code", None)     
    
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

    data = {
        "username": user_info_json['name'],
        "email": user_info_json['email']
    }
    
    serializer = OAuthSerializer(data=data)
    if serializer.is_valid(raise_exception=True):
        user = serializer.validated_data["user"]
        access_token = serializer.validated_data["access_token"]
        refresh_token = serializer.validated_data["refresh_token"]

        res = JsonResponse(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
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

# -- TeamMember 관련 뷰 --
class TeamMemberCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=TeamMemberSerializer,
        responses={201: "team member created"}
    )
    def post(self, request):
        serializer = TeamMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            team_member = serializer.save()
        except ValidationError as e:
            # 모델에서 발생한 ValidationError를 400으로 반환
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(TeamMemberSerializer(team_member).data, status=status.HTTP_201_CREATED)

class TeamMemberListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        team_members = TeamMember.objects.all()
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)