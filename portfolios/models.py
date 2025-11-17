from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from django.apps import apps
import pytz
from datetime import datetime, time

class Project(models.Model):
    project_name = models.CharField(max_length=10)
    date_start = models.DateField()
    date_end = models.DateField()
    owner = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def project_duration(self):
        return (self.date_end - self.date_start).days + 1

    def clean(self):
        # start가 end보다 뒤라면 ValidationError 발생
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise ValidationError("시작일은 종료일보다 이후일 수 없습니다.")
        
        # 프로젝트 이름 길이 제한
        if self.project_name and len(self.project_name) > 10:
            raise ValidationError("프로젝트 이름은 최대 10자까지 가능합니다.")
    
    def save(self, *args, **kwargs):
        # full_clean()으로 clean() 포함 모든 validator 실행
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.project_name

class Log(models.Model):
    REASONS = (
        ("DAILY_COMPLETE", "데일리 기록 완료"),
        ("TAG_REVIEW_COMPLETE", "태깅 리뷰 완료"),
    )

    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.localdate)
    reason = models.CharField(max_length=30, choices=REASONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "project", "reason", "created_at"])
        ]

    # 하루 최대 2개 통나무 지급 함수
    @classmethod
    def give_log(cls, user, project, reason):
        kr_tz = pytz.timezone("Asia/Seoul")
        now_kr = timezone.now().astimezone(kr_tz)
        today_kr = now_kr.date()

        valid_reasons = dict(cls.REASONS).keys()
        if reason not in valid_reasons:
            raise ValueError("잘못된 통나무 지급 사유입니다.")
        
        start_kr = kr_tz.localize(datetime.combine(today_kr, time.min))
        end_kr = kr_tz.localize(datetime.combine(today_kr, time.max))
        
        already_given = cls.objects.filter(
            user=user,
            project=project,
            reason=reason,
            created_at__gte=start_kr.astimezone(timezone.utc),
            created_at__lte=end_kr.astimezone(timezone.utc),
        ).exists()

        if already_given:
            return {"success": False, "message": f"이미 오늘 {reason} 보상을 받았습니다."}

        log = cls.objects.create(
            user=user,
            project=project,
            date=today_kr,
            reason=reason
        )

        house = ProjectHouse.objects.get(project=project)
        house.update_progress()

        return {"success": True, "message": f"통나무 지급 성공 ({reason})"}


class ProjectHouse(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    difficulty_ratio = models.FloatField(default=0.85)  # R = 0.85
    total_required_logs = models.PositiveIntegerField(default=0)
    current_logs = models.PositiveIntegerField(default=0)

    def calculate_required_logs(self):
        TeamMember = apps.get_model('accounts', 'TeamMember')
        member_count = TeamMember.objects.filter(project=self.project).count()
        duration = self.project.project_duration()
        return int(member_count * duration * 2 * self.difficulty_ratio)

    def update_progress(self):
        self.current_logs = Log.objects.filter(project=self.project).count()
        self.total_required_logs = self.calculate_required_logs()
        self.save()

    @property
    def progress_percent(self):
        if self.total_required_logs == 0:
            return 0
        return round((self.current_logs / self.total_required_logs) * 100, 1)
