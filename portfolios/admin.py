from django.contrib import admin
from .models import Project, TagStyle, Log, ProjectHouse

admin.site.register(Project)
admin.site.register(TagStyle)
admin.site.register(Log)
admin.site.register(ProjectHouse)
