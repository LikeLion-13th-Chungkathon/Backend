from django.db import models
from accounts.models import User
from memos.models import Memo
from portfolios.models import TagStyle
from django.core.exceptions import ValidationError

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True) # 객체를 생성할 때 날짜와 시간 저장
    modified_at = models.DateTimeField(auto_now=True)  # 객체를 저장할 때 날짜와 시간 갱신

    class Meta:
        abstract = True

class Tagging(BaseModel):
    id = models.AutoField(primary_key=True)
    tag_style = models.ForeignKey(TagStyle, on_delete=models.CASCADE, related_name="taggings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="taggings")
    memo = models.ForeignKey(Memo, on_delete=models.CASCADE, related_name="taggings")
    tag_contents = models.CharField(max_length=20)
    offset_start = models.PositiveIntegerField(default=0)
    offset_end = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.offset_start > self.offset_end:
            raise ValidationError("offset_start는 offset_end보다 클 수 없습니다.")