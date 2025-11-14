from django.db import models
from accounts.models import User
from portfolios.models import Project

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True) # 객체를 생성할 때 날짜와 시간 저장
    modified_at = models.DateTimeField(auto_now=True)  # 객체를 저장할 때 날짜와 시간 갱신

    class Meta:
        abstract = True


class Memo(BaseModel):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memos")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memos")
    date = models.DateField()
    contents = models.TextField(default="", max_length=500)
