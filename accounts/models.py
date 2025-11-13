from django.db import models
from django.contrib.auth.models import AbstractUser
from portfolios.models import Project
from django.core.exceptions import ValidationError

class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    nickname = models.CharField(max_length=30, unique=True, null=True, blank=True)

    @staticmethod
    def get_user_by_email(email):
        try:
            return User.objects.get(email=email)
        except Exception:
            return None

class TeamMember(models.Model):

    Roles = (('Admin', '팀장'), ('Member', '팀원'))
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Roles)
    joined_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # 현재 프로젝트에 속한 팀원 수 체크
        if self.project and TeamMember.objects.filter(project=self.project).count() >= 6:
            raise ValidationError("한 프로젝트에는 최대 6명까지만 참여할 수 있습니다.")

    def save(self, *args, **kwargs):
        # clean() 포함 모든 검증 실행
        self.full_clean()
        super().save(*args, **kwargs)