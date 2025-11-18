from django.db import models
from accounts.models import User
from memos.models import Memo
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True) # 객체를 생성할 때 날짜와 시간 저장
    modified_at = models.DateTimeField(auto_now=True)  # 객체를 저장할 때 날짜와 시간 갱신

    class Meta:
        abstract = True

# RGB 검증
HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message="올바른 HEX 색상 코드를 입력하세요 (예: #AABBCC)",
)

class TagStyle(models.Model):
    id = models.AutoField(primary_key=True)
    tag_detail = models.CharField(max_length=20, unique=True)
    tag_color = models.CharField(max_length=7, unique=True, validators=[HEX_COLOR_VALIDATOR])

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(fields=["project", "tag_detail"], name="unique_tag_detail_per_project"),
    #         models.UniqueConstraint(fields=["project", "tag_color"], name="unique_tag_color_per_project"),
    #     ]

class Tagging(BaseModel):
    id = models.AutoField(primary_key=True)
    tag_style = models.ForeignKey(TagStyle, on_delete=models.CASCADE, related_name="taggings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="taggings")
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name="taggings")
    tag_contents = models.CharField(max_length=500)
    offset_start = models.PositiveIntegerField(default=0)
    offset_end = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.offset_start > self.offset_end:
            raise ValidationError("offset_start는 offset_end보다 클 수 없습니다.")
        
    def save(self, *args, **kwargs):
        # full_clean()으로 clean() 포함 모든 validator 실행
        self.full_clean()
        super().save(*args, **kwargs)