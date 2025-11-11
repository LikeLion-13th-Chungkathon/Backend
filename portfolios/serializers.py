from rest_framework import serializers
from .models import *
import uuid  # 초대 코드 생성을 위해 uuid 모듈 추가

class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['project_name', 'date_start', 'date_end']
        read_only_fields = ['owner', 'invite_code']

    def create(self, validated_data):
        """
        Project 생성 요청 시, 고유한 invite_code를 생성하여 함께 저장합니다.
        """
        
        # 1. 고유한 초대 코드 생성 (예: uuid4의 앞 10자리)
        # 10자리로 했지만, models.py의 max_length(20) 안에서 자유롭게 정할 수 있습니다.
        invite_code = str(uuid.uuid4().hex)[:10]
        
        # 2. (낮은 확률이지만) 코드가 중복되지 않는지 확인
        while Project.objects.filter(invite_code=invite_code).exists():
            invite_code = str(uuid.uuid4().hex)[:10]
            
        # 3. validated_data에 초대 코드와 view에서 받은 owner를 추가하여 Project 객체 생성
        # view의 .save(owner=request.user)에서 넘겨준 owner가 validated_data에 포함되어 있습니다.
        project = Project.objects.create(
            **validated_data,
            invite_code=invite_code
        )
        
        return project
    
# 프로젝트 조회 및 수정을 위한 시리얼라이져
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        
        # 'id'를 포함한 모든 필드를 기본으로 합니다.
        fields = ['id', 'project_name', 'date_start', 'date_end', 
                  'owner', 'invite_code', 'created_at']
        
        # 중요: 수정(PUT, PATCH) 요청 시, 아래 필드들은
        # '읽기 전용'으로 설정하여 수정되지 않도록 합니다.
        read_only_fields = ['id', 'owner', 'invite_code', 'created_at']


class TagStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagStyle
        fields = ["id", "project", "tag_detail", "tag_color"]
        read_only_fields = ["id", "project"]
