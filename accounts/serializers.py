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
    
class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['user', 'project', 'role', 'joined_at']