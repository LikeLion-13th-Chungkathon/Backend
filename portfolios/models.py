from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

class Project(models.Model):
    project_name = models.CharField(max_length=100)
    date_start = models.DateField()
    date_end = models.DateField()
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        # start가 end보다 뒤라면 ValidationError 발생
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise ValidationError("시작일은 종료일보다 이후일 수 없습니다.")
    
    def save(self, *args, **kwargs):
        # full_clean()으로 clean() 포함 모든 validator 실행
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.project_name
    
# RGB 검증
HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#[0-9a-fA-F]{6}$",
    message="올바른 HEX 색상 코드를 입력하세요 (예: #AABBCC)",
)

class TagStyle(models.Model):
    id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tag_styles")
    tag_detail = models.CharField(max_length=20)
    tag_color = models.CharField(max_length=7, validators=[HEX_COLOR_VALIDATOR])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["project", "tag_detail"], name="unique_tag_detail_per_project"),
            models.UniqueConstraint(fields=["project", "tag_color"], name="unique_tag_color_per_project"),
        ]
