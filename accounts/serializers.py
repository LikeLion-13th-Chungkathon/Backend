from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken


# 회원가입용 시리얼라이저
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(required=True)
    # 클라이언트 레벨에서 username 길이 제한을 강제합니다 (예: 30자)
    username = serializers.CharField(required=True, max_length=30)
    email = serializers.CharField(required=True)

    class Meta:
        model = User

        # 필요한 필드값만 지정, 회원가입은 email까지 필요, 실행순서: username -> email -> password
        fields = ['username', 'email', 'password']

    # create 재정의 (Overriding)
    def create(self, validated_data):
        # 비밀번호 분리
        password = validated_data.pop('password')

        # user 객체 생성
        user = User(**validated_data)

        # 비밀번호는 해싱해서 저장
        user.set_password(password)
        user.save()

        return user
    
    # 이메일 유효성 검사
    def validate_email(self, value):

         # 이메일 형식이 맞는지 검사
        if not "@" in value:
            raise serializers.ValidationError("유효하지 않은 이메일 형식입니다.")

        # 이메일 중복 여부 검사
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이메일이 이미 존재합니다.")

        return value

    def validate_username(self, value):
        if len(value) > 10:
            raise serializers.ValidationError("사용자 이름은 10자 이내여야 합니다.")

        # 중복 검사
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("사용자 이름이 이미 존재합니다.")

        return value
    
class AuthSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required = True)
    password = serializers.CharField(required = True)

    class Meta:
        model = User

        # 로그인은 username과 password만 필요
        fields = ['username', 'password']

    # 로그인 유효성 검사 함수
    def validate(self, data):
        username = data.get('username', None)
        password = data.get('password', None)
		    
		# username으로 사용자 찾는 모델 함수
        user = User.objects.filter(username=username).first()
        
        # 존재하는 회원인지 확인
        if user is None:
            raise serializers.ValidationError("User does not exist.")
        else:
			      # 비밀번호 일치 여부 확인
            if not user.check_password(password):
                raise serializers.ValidationError("Wrong password.")
        
        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        data = {
            "user": user,
            "refresh_token": refresh_token,
            "access_token": access_token,
        }

        return data
    
# OAuth 시리얼라이저 (Google 회원가입/로그인 용도)
class OAuthSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    email = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username','email']

    def validate(self, data):
        username = data.get('username', None)
        email = data.get('email', None)

        if email is None:
            raise serializers.ValidationError('Email does not exist.')
        
        user = User.get_user_by_email(email=email)
        
        # 존재하지 않는 회원이면 새롭게 가입
        if user is None:
            user = User.objects.create(username=username, email=email)

        token = RefreshToken.for_user(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        data = {
            "user": user,
            "refresh_token": refresh_token,
            "access_token": access_token,
        }

        return data
    
# 닉네임을 포함한 Google 신규 회원가입 전용 시리얼라이저
class GoogleSignupSerializer(serializers.ModelSerializer):
    """
    신규 Google 유저의 회원가입을 처리합니다.
    닉네임(필수), 이메일(필수), Google이름(username_from_google)을 받습니다.
    """
    email = serializers.EmailField(required=True)
    nickname = serializers.CharField(required=True)
    # 프론트에서 username_from_google 라는 key로 Google 이름을 받아옵니다.
    # write_only=True: 이 필드는 오직 쓰기(역직렬화)에만 사용됨을 의미합니다.
    username_from_google = serializers.CharField(required=True, write_only=True) 

    class Meta:
        model = User
        # 실제 User 모델에 저장할 필드 (username은 내부에서 생성)
        fields = ['email', 'nickname', 'username_from_google'] 

    def validate_email(self, value):
        """이메일 중복 검사"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return value

    def validate_nickname(self, value):
        """닉네임 중복 검사 (모델의 unique=True와 별개로 시리얼라이저단에서 확인)"""
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("This nickname is already taken.")
        return value

    def _create_unique_username(self, base_name):
        """
        Google이 제공한 이름(base_name)을 기반으로 고유한 username을 생성합니다.
        (AbstractUser의 username은 unique=True여야 함)
        """
        username = base_name
        count = 1
        # "홍길동" -> "홍길동_1", "홍길동_2" ...
        while User.objects.filter(username=username).exists():
            username = f"{base_name}_{count}"
            count += 1
        return username

    def save(self, **kwargs):
        """
        create 메서드를 직접 호출하는 대신, save를 오버라이드하여
        유저 생성과 토큰 발급을 한 번에 처리하고 뷰로 반환합니다.
        """
        validated_data = self.validated_data
        
        email = validated_data['email']
        nickname = validated_data['nickname']
        username_from_google = validated_data['username_from_google']

        # Google 이름을 기반으로 고유한 username 생성
        unique_username = self._create_unique_username(username_from_google)

        # User 생성 (AbstractUser의 create_user 사용)
        user = User.objects.create_user(
            username=unique_username,
            email=email,
            nickname=nickname
            # OAuth 유저는 별도 비밀번호가 필요 없습니다.
        )

        # 토큰 생성
        token = RefreshToken.for_user(user)
        access_token = str(token.access_token)
        refresh_token = str(token)

        # 뷰에서 필요한 데이터를 딕셔너리로 반환
        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "nickname", "created_at"]

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['user', 'project', 'role', 'joined_at']


