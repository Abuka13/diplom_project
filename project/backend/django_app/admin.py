from django.contrib import admin
from django_app import models

admin.site.site_header = "Панель управления"  # default: "Django Administration"
admin.site.index_title = "Администрирование сайта"  # default: "Site administration"
admin.site.site_title = "Администрирование"  # default: "Django site admin"

admin.site.register(models.UserAuthToken)
admin.site.register(models.BusIdea)
admin.site.register(models.IdeaRatings)
admin.site.register(models.Ideacomments)
admin.site.register(models.Resume)
admin.site.register(models.Room)
admin.site.register(models.Message)
admin.site.register(models.Product)
