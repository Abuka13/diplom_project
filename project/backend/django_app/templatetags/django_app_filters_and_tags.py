from django import template
import datetime
from django.contrib.auth.models import User, Group
from django.http import HttpRequest

from django_app import models

# Фильтры и тэги (jinja)
# Для изменения отображения данных в шаблоне, для логики внутри шаблонов

# 0. strftime
# 1. Смена округления
# 2. Сменить запятую на точку, и наоборот (разные языки)
# 3. Формат с разделителями (раздение числа при слишком больших значениях)
# 4. Нужно написать тэг, который проверяет группы у пользователя


register = template.Library()


@register.simple_tag(takes_context=True)
def i_liked_this_post(context: str, post_pk: str) -> int:
    try:
        request: HttpRequest = context["request"]
        idea = models.BusIdea.objects.get(id=int(post_pk))

        ratings = models.IdeaRatings.objects.filter(idea=idea, author=request.user)
        if len(ratings) < 1:
            return 0
        else:
            rating = ratings[0]
            if rating.status:
                return 1
            return -1
    except Exception as error:
        print("error simple_tag i_liked_this_post: ", error)
        return 0

@register.simple_tag(takes_context=True)
def i_liked_this_resume(context: str, post_pk: str) -> int:
    try:
        request: HttpRequest = context["request"]
        resume = models.Resume.objects.get(id=int(post_pk))

        ratings = models.ResumeRatings.objects.filter(resume=resume, author=request.user)
        if len(ratings) < 1:
            return 0
        else:
            rating = ratings[0]
            if rating.status:
                return 1
            return -1
    except Exception as error:
        print("error simple_tag i_liked_this_post: ", error)
        return 0