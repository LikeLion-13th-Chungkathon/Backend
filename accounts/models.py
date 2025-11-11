from django.db import models
from django.contrib.auth.models import AbstractUser
from portfolios.models import Project
class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class TeamMember(models.Model):

    Roles = (('Admin', '팀장'), ('Member', '팀원'))
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=Roles)
    joined_at = models.DateTimeField(auto_now_add=True)