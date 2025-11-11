from django.db import models
from accounts.models import User

class Project(models.Model):
    project_name = models.CharField(max_length=100)
    date_start = models.DateField()
    date_end = models.DateField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    invite_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.project_name