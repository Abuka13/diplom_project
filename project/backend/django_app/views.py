import os
import re
import random

from django.db.models import Count, F, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.cache import caches, cache
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django_app import models
from django_app.models import UserAuthToken, Product
import psycopg2
from django.db import connection
from django.contrib.auth.decorators import user_passes_test
import requests
from bs4 import BeautifulSoup
from django_app import utils
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from . import serializers, models
from .serializers import ProductSerializer
import requests
import threading
from django_app import tasks as django_app_celery
from django_settings.celery import app as current_celery_app
from celery.result import AsyncResult



RamCache = caches["default"]
DatabaseCache = caches["extra"]
def home(request: HttpRequest) -> HttpResponse:

    return render(request, "home.html")



#TODO АУТЕНТИФИКАЦИЯ
def register(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return render(request, "register.html")
    elif request.method == "POST":
        username = request.POST.get('username')
        name = request.POST.get('name')
        surname = request.POST.get('surname')
        email = str(request.POST.get("email", None)).strip()  # Admin1@gmail.com
        password = str(request.POST.get("password", None)).strip()  # Admin1@gmail.com
        valid_email = re.match(r"[A-Za-z0-9._-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", email)
        valid_password = re.match(r"^.*(?=.{8,})(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=!.]).*$", password)
        User.objects.create(
            username=username,
            password=make_password(password),
            first_name=name,
            last_name=surname,
            email=email
        )
        return redirect(login_f)
    else:
        raise Exception("Method not allowed!")
@login_required
def logout_(request: HttpRequest) -> HttpResponse:
    logout(request)
    return redirect(reverse("home"))
def login_f(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            token = UserAuthToken.get_or_generate_token(request, user)
            login(request, user)
            return redirect(home_l)
        else:
            raise Exception("Данные для входа неправильные!")
    else:
        raise Exception("Method not supported")

@login_required
def home_l(request):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.0.0 Safari/537.36'
    }
    photos_folder = 'static/media/photos'
    photo_files = os.listdir(photos_folder)

    selected_photos = random.sample(photo_files, 3)
    cached_data = cache.get('news_data')
    if cached_data is not None:
        data2 = cached_data
    else:
        data1 = requests.get("https://fakenews.squirro.com/news/sport", headers=headers).json()
        _news = data1.get("news", [])
        data2 = [{"id": new["id"], "title": new["headline"], "author": new["author"]} for new in _news][:3]
        cache.set('news_data', data2, timeout=3600)

    return render(request, "home_l.html",{'data2': data2,'selected_photos': selected_photos})


def is_moderator(user):
    return user.is_staff

#TODO CRUD
@login_required
def idea_create(request):
    if request.method == "GET":
        return render(request, "send_idea.html", context={})
    elif request.method == "POST":

        title = str(request.POST["title"])
        description = str(request.POST["description"])
        image = request.FILES["image"]
        file = request.FILES["file"]
        date = str(request.POST["date"])
        models.BusIdea.objects.create(
            author=request.user,
            title=title,
            description=description,
            image=image,
            file=file,
            datetime=date,
        )
        return redirect(home_l)
    else:
        raise Exception("Method not allowed!")


@login_required
@user_passes_test(is_moderator)
def idea_delete(request: HttpRequest, pk: str):
    if request.method == "GET":
        idea = models.BusIdea.objects.get(id=int(pk))
        idea.delete()
        return redirect(list_ideas)
    else:
        raise Exception("Method not allowed!")

@login_required
def idea_detail(request: HttpRequest, pk: str) -> HttpResponse:
    idea = models.BusIdea.objects.get(id=int(pk))
    comments = models.Ideacomments.objects.filter(idea=idea)
    ratings = models.IdeaRatings.objects.filter(idea=idea)
    ratings = {
        "like": ratings.filter(status=True).count(),
        "dislike": ratings.filter(status=False).count(),
        "total": ratings.filter(status=True).count() - ratings.filter(status=False).count(),
    }

    return render(request, "idea_detail.html",{"idea": idea, "ratings": ratings, "comments": comments})

@login_required
def idea_comment_create(request: HttpRequest, pk: str) -> HttpResponse:
    idea = models.BusIdea.objects.get(id=int(pk))
    text = request.POST.get("text", "")
    models.Ideacomments.objects.create(idea=idea, author=request.user, text=text)

    return redirect(reverse("idea_detail", args=(pk,)))

@login_required
def idea_rating(request: HttpRequest, pk: str, is_like: str) -> HttpResponse:
    idea = models.BusIdea.objects.get(id=int(pk))
    is_like = True if str(is_like).lower().strip() == "лайк" else False

    ratings = models.IdeaRatings.objects.filter(idea=idea, author=request.user)
    if len(ratings) < 1:
        models.IdeaRatings.objects.create(idea=idea, author=request.user, status=is_like)
    else:
        rating = ratings[0]
        if is_like == True and rating.status == True:
            rating.delete()
        elif is_like == False and rating.status == False:
            rating.delete()
        else:
            rating.status = is_like
            rating.save()

    return redirect(reverse("idea_detail", args=(pk,)))

@login_required
def list_ideas(request: HttpRequest) -> HttpResponse:
    ideas = models.BusIdea.objects.all()
    selected_page = request.GET.get(key="page", default=1)
    limit_post_by_page = 3
    paginator = Paginator(ideas, limit_post_by_page)
    current_page = paginator.get_page(selected_page)
    return render(request, "list_ideas.html", context={"current_page": current_page})

@login_required
@user_passes_test(is_moderator)
def idea_edit(request, pk):
    if request.method == "GET":
        return render(request, "idea_update.html")
    elif request.method == "POST":

        idea = models.BusIdea.objects.get(id=int(pk))
        title = str(request.POST["title"])
        description = str(request.POST["description"])
        image = request.FILES["image"]
        file = request.FILES["file"]
        date = str(request.POST["date"])
        idea.title = title
        idea.description = description
        idea.image = image
        idea.file = file
        idea.datetime = date

        idea.save()
        return redirect(list_resumes)

@login_required
def display_top_ideas(request):
    ideas_with_ratings = models.BusIdea.objects.annotate(
        num_likes=Count('idearatings', filter=Q(idearatings__status=True)),
        num_dislikes=Count('idearatings', filter=Q(idearatings__status=False))
    )

    ideas_with_ratings = ideas_with_ratings.annotate(
        total_rating=F('num_likes') - F('num_dislikes')
    )

    sorted_ideas = ideas_with_ratings.order_by('-total_rating')

    top_ideas = sorted_ideas[:3]  # Получаем первые три идеи с наивысшим рейтингом

    return render(request, 'top_ideas.html', {'top_ideas': top_ideas})





@login_required
def vacancy_list(request):
    connection = psycopg2.connect(
        user="postgres",
        password="Takanashi_13",
        host="127.0.0.1",  # localhost - 192.168.1.100
        port="5432",
        dbname="vacancies",
    )
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM vacancy")
    vacancies = cursor.fetchall()
    _vacancies = []
    for vacancy in vacancies:
        new_dict = {
            "id": vacancy[0],
            "title": vacancy[1],
            "duties": vacancy[2][:15:1] + "..." if len(vacancy[2]) > 15 else vacancy[2],
            "conditions": vacancy[3][:15:1] + "..." if len(vacancy[3]) > 15 else vacancy[3],
            "salary": vacancy[4],
            "company": vacancy[5],
            "active": vacancy[6],

        }
        _vacancies.append(new_dict)
    selected_page = request.GET.get(key="page", default=1)
    limit_post_by_page = 3
    paginator = Paginator(_vacancies, limit_post_by_page)
    current_page = paginator.get_page(selected_page)

    return render(request, 'vacancy_list.html',context={"current_page": current_page})
@login_required
@user_passes_test(is_moderator)
def vacancy_delete(request, pk: str):
    connection = psycopg2.connect(
        user="postgres",
        password="Takanashi_13",
        host="127.0.0.1",  # localhost - 192.168.1.100
        port="5432",
        dbname="vacancies",
    )
    cursor = connection.cursor()
    cursor.execute("DELETE FROM vacancy WHERE id = %s;", (pk,))

    return redirect('vacancy_list')

@login_required
def vacancy_detail(request, pk: str):
    connection = psycopg2.connect(
        user="postgres",
        password="Takanashi_13",
        host="127.0.0.1",  # localhost - 192.168.1.100
        port="5432",
        dbname="vacancies",
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vacancy WHERE id = %s;", (pk,))
    vacancy = cursor.fetchone()


    new_dict = {
        "id": str(vacancy[0]),
        "title": vacancy[1],
        "duties": vacancy[2][:15:1] + "..." if len(vacancy[2]) > 15 else vacancy[2],
        "conditions": vacancy[3][:15:1] + "..." if len(vacancy[3]) > 15 else vacancy[3],
        "salary": vacancy[4],
        "company": vacancy[5],
        "active": vacancy[6],

    }



    return render(request, 'vacancy_detail.html', {'vacancy': new_dict})
@login_required
def vacancy_create(request):
    if request.method == 'GET':
        return render(request, 'vacancy_form.html')
    connection = psycopg2.connect(
        user="postgres",
        password="Takanashi_13",
        host="127.0.0.1",  # localhost - 192.168.1.100
        port="5432",
        dbname="vacancies",
    )
    cursor = connection.cursor()
    if request.method == 'POST':
        company = request.POST['company']
        title = request.POST['title']
        duties = request.POST['duties']
        conditions = request.POST['conditions']
        salary = int(request.POST['salary'])
        active = False

        query = """INSERT INTO vacancy (title,duties, conditions,salary,company,active)
                           VALUES (%s, %s, %s, %s, %s, %s);"""
        data = (title,duties, conditions,salary,company,active)

        cursor.execute(query, data)
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(home_l)

@login_required
@user_passes_test(is_moderator)
def vacancy_edit(request, pk):
    if request.method == 'GET':
        connection = psycopg2.connect(
            user="postgres",
            password="Takanashi_13",
            host="127.0.0.1",
            port="5432",
            dbname="vacancies",
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM vacancy WHERE id = %s;", (pk,))
        vacancy = cursor.fetchone()
        cursor.close()
        connection.close()
        vacancy_data = {
            "id": vacancy[0],
            "title": vacancy[1],
            "duties": vacancy[2],
            "conditions": vacancy[3],
            "salary": vacancy[4],
            "company": vacancy[5],
            "active": vacancy[6],
        }

        return render(request, 'vacancy_update.html', {'vacancy': vacancy_data})
    elif request.method == 'POST':
        connection = psycopg2.connect(
            user="postgres",
            password="Takanashi_13",
            host="127.0.0.1",  # localhost - 192.168.1.100
            port="5432",
            dbname="vacancies",
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM vacancy WHERE id = %s;", (pk,))
        vacancy = cursor.fetchone()
        id =str(vacancy[0])
        title = request.POST['title']
        duties = request.POST['duties']
        conditions = request.POST['conditions']
        salary = request.POST['salary']
        company = request.POST['company']
        active = False

        query = "UPDATE vacancy SET title=%s, duties=%s, conditions=%s, salary=%s, company=%s, active=%s WHERE id=%s;"
        data = (title,duties, conditions,salary,company,active,id)
        cursor.execute(query, data)
        connection.commit()
        cursor.close()
        connection.close()
        return redirect('vacancy_detail', pk=pk)


#TODO Онлайн-Чат
def rooms(request):
    return render(request, "home_l.html", context={"rooms": models.Room.objects.all()})


@login_required
def room(request, slug):
    room_obj = models.Room.objects.get(slug=slug)
    messages = models.Message.objects.filter(room=room_obj)[:2][::-1]
    return render(
        request,
        "room.html",
        context={"room": room_obj, "messages": messages}
    )

#TODO Resume
@login_required
def resume_create(request):
    if request.method == "GET":
        return render(request, "resume_create.html", context={})
    elif request.method == "POST":
        post = str(request.POST["post"])
        fullname = str(request.POST["full_name"])
        phone_number = str(request.POST["phone_number"])
        skills = str(request.POST["skills"])
        experience = str(request.POST["experience"])
        education = str(request.POST["education"])
        models.Resume.objects.create(
            post = post,
            full_name=fullname,
            phone_number=phone_number,
            skills=skills,
            experience=experience,
            education=education,
        )
        return redirect(home_l)
    else:
        raise Exception("Method not allowed!")
@login_required
@user_passes_test(is_moderator)
def resume_delete(request: HttpRequest, pk: str):
    if request.method == "GET":
        resume = models.Resume.objects.get(id=int(pk))
        resume.delete()
        return redirect(list_resumes)
    else:
        raise Exception("Method not allowed!")

@login_required
def resume_detail(request: HttpRequest, pk: str) -> HttpResponse:
    resume = models.Resume.objects.get(id=int(pk))
    comments = models.Resumecomments.objects.filter(resume=resume)
    ratings = models.ResumeRatings.objects.filter(resume=resume)
    ratings = {
        "like": ratings.filter(status=True).count(),
        "dislike": ratings.filter(status=False).count(),
        "total": ratings.filter(status=True).count() - ratings.filter(status=False).count(),
    }

    return render(request, "resume_detail.html",{"resume": resume, "ratings": ratings, "comments": comments})

@login_required
def resume_comment_create(request: HttpRequest, pk: str) -> HttpResponse:
    resume = models.Resume.objects.get(id=int(pk))
    text = request.POST.get("text", "")
    models.Resumecomments.objects.create(resume=resume, author=request.user, text=text)

    return redirect(reverse("resume_detail", args=(pk,)))

@login_required
def resume_rating(request: HttpRequest, pk: str, is_like: str) -> HttpResponse:
    resume = models.Resume.objects.get(id=int(pk))
    is_like = True if str(is_like).lower().strip() == "лайк" else False

    ratings = models.ResumeRatings.objects.filter(resume=resume, author=request.user)
    if len(ratings) < 1:
        models.ResumeRatings.objects.create(resume=resume, author=request.user, status=is_like)
    else:
        rating = ratings[0]
        if is_like == True and rating.status == True:
            rating.delete()
        elif is_like == False and rating.status == False:
            rating.delete()
        else:
            rating.status = is_like
            rating.save()

    return redirect(reverse("resume_detail", args=(pk,)))

@login_required
def list_resumes(request: HttpRequest) -> HttpResponse:
    resumes = models.Resume.objects.all()
    selected_page = request.GET.get(key="page", default=1)
    limit_post_by_page = 3
    paginator = Paginator(resumes, limit_post_by_page)
    current_page = paginator.get_page(selected_page)
    return render(request, "resume_list.html", context={"current_page": current_page})

@login_required
def get_coin(request):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/102.0.0.0 Safari/537.36'
    }
    html_content = """
        <tr class="CoinsListstyles__Item-sc-1c8245s-18 dDoMMr"><td data-gtm-ec="crypto-catalog" data-gtm-el="btc" data-gtm-ea="add-to-favourites" class="CoinsListstyles__FavoritesWrapper-sc-1c8245s-19 cFOWmO"><svg width="14px" height="14px" viewBox="0 0 20 19" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="star" class="Favoritesstyles__StarIcon-sc-s11y3p-0 bJXTKh"><path d="m6.85 14.825 3.15-1.9 3.15 1.925-.825-3.6 2.775-2.4-3.65-.325-1.45-3.4L8.55 8.5l-3.65.325 2.775 2.425-.825 3.575ZM3.825 19l1.625-7.025L0 7.25l7.2-.625L10 0l2.8 6.625 7.2.625-5.45 4.725L16.175 19 10 15.275 3.825 19Z" fill="currentColor"></path></svg></td><td class="CoinsListstyles__CoinInfo-sc-1c8245s-20 bynNLe"><div class="CoinsListstyles__ImageWrapper-sc-1c8245s-21 fescup"><span style="box-sizing: border-box; display: inline-block; overflow: hidden; width: initial; height: initial; background: none; opacity: 1; border: 0px; margin: 0px; padding: 0px; position: relative; max-width: 100%;"><span style="box-sizing: border-box; display: block; width: initial; height: initial; background: none; opacity: 1; border: 0px; margin: 0px; padding: 0px; max-width: 100%;"><img alt="" aria-hidden="true" src="data:image/svg+xml,%3csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20version=%271.1%27%20width=%2732%27%20height=%2732%27/%3e" style="display: block; max-width: 100%; width: initial; height: initial; background: none; opacity: 1; border: 0px; margin: 0px; padding: 0px;"></span><img alt="Bitcoin" src="/crypto/_next/image?url=https%3A%2F%2Fassets.coingecko.com%2Fcoins%2Fimages%2F1%2Flarge%2Fbitcoin.png%3F1696501400&amp;w=64&amp;q=100" decoding="async" data-nimg="intrinsic" srcset="/crypto/_next/image?url=https%3A%2F%2Fassets.coingecko.com%2Fcoins%2Fimages%2F1%2Flarge%2Fbitcoin.png%3F1696501400&amp;w=32&amp;q=100 1x, /crypto/_next/image?url=https%3A%2F%2Fassets.coingecko.com%2Fcoins%2Fimages%2F1%2Flarge%2Fbitcoin.png%3F1696501400&amp;w=64&amp;q=100 2x" style="position: absolute; inset: 0px; box-sizing: border-box; padding: 0px; border: none; margin: auto; display: block; width: 0px; height: 0px; min-width: 100%; max-width: 100%; min-height: 100%; max-height: 100%;"><noscript></noscript></span></div><div class="CoinsListstyles__NameWrapper-sc-1c8245s-22 gyyOTf"><p class="CoinsListstyles__Code-sc-1c8245s-24 lgioIM">btc</p><p class="CoinsListstyles__Name-sc-1c8245s-23 kVPjIs">Bitcoin</p></div></td><td class="CoinsListstyles__Price-sc-1c8245s-25 fYNuHQ">$37&nbsp;300</td><td class="CoinsListstyles__Percent-sc-1c8245s-26 ldQCwT">▼ -0,43%</td><td class="CoinsListstyles__MarketCap-sc-1c8245s-27 kLgrwU">
                    $
                    732&nbsp;млрд
                    </td><td class="CoinsListstyles__ButtonWrapper-sc-1c8245s-29 hZOcKN"><button data-gtm-ec="crypto-catalog" data-gtm-el="btc" data-gtm-ea="order-button" data-gtm-show="show" class="CoinsListstyles__ButtonBuy-sc-1c8245s-30 kiNJlC" data-gtm-vis-first-on-screen6361938_389="828" data-gtm-vis-total-visible-time6361938_389="100" data-gtm-vis-has-fired6361938_389="1" data-gtm-vis-first-on-screen6361938_904="832" data-gtm-vis-total-visible-time6361938_904="100" data-gtm-vis-has-fired6361938_904="1">Купить</button></td></tr>
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract cryptocurrency information
    crypto_info = {}
    # Extracting data-gtm attributes from td with class CoinsListstyles__CoinInfo-sc-1c8245s-20
    coin_info_td = soup.find('td', class_='CoinsListstyles__CoinInfo-sc-1c8245s-20')
    crypto_info['code'] = coin_info_td.find('p', class_='CoinsListstyles__Code-sc-1c8245s-24').text.strip()
    crypto_info['name'] = coin_info_td.find('p', class_='CoinsListstyles__Name-sc-1c8245s-23').text.strip()

    # Extracting data from td with class CoinsListstyles__Price-sc-1c8245s-25
    crypto_info['price'] = soup.find('td', class_='CoinsListstyles__Price-sc-1c8245s-25').text.strip()

    # Extracting data from td with class CoinsListstyles__Percent-sc-1c8245s-26
    crypto_info['percent_change'] = soup.find('td', class_='CoinsListstyles__Percent-sc-1c8245s-26').text.strip()

    # Extracting data from td with class CoinsListstyles__MarketCap-sc-1c8245s-27
    crypto_info['market_cap'] = soup.find('td', class_='CoinsListstyles__MarketCap-sc-1c8245s-27').text.strip()
    return render(request, 'market.html', {'crypto_info':crypto_info})


@login_required
@user_passes_test(is_moderator)
def resume_edit(request, pk):
    if request.method == "GET":
        return render(request, "resume_update.html")
    elif request.method == "POST":

        resume = models.Resume.objects.get(id=int(pk))
        post = str(request.POST["post"])
        fullname = str(request.POST["full_name"])
        phone_number = str(request.POST["phone_number]"])
        skills = str(request.POST["skills"])
        experience = str(request.POST["experience"])
        education = str(request.POST["education"])
        resume.post = post
        resume.full_name = fullname
        resume.phone_number = phone_number
        resume.skills = skills
        resume.experience = experience
        resume.education = education
        resume.save()
        return redirect(list_resumes)


#TODO DRF
response_schema_dict = {
    "200": openapi.Response(
        description="custom 200 description",
        examples={
            "application/json": {
                "200_key1": "200_value_1",
                "200_key2": "200_value_2",
            }
        },
    ),
    "205": openapi.Response(
        description="custom 205 description",
        examples={
            "application/json": {
                "205_key1": "205_value_1",
                "205_key2": "205_value_2",
            }
        },
    ),
    "205": openapi.Response(
        description="custom 205 description",
        examples={
            "application/json": {
                "205_key1": "205_value_1",
                "205_key2": "205_value_2",
            }
        },
    ),
}
@swagger_auto_schema(  # документация
    method="GET",
    manual_parameters=[
        openapi.Parameter("search_by", openapi.IN_QUERY, description="Поиск по этому параметру", type=openapi.TYPE_STRING, default="")
    ],  # Описание входных данных
    responses={200: serializers.ProductSerializer, 400: "Error detail"},  # Описание выходных данных
)
@api_view(['GET'])
def products(request):
    new =  Product.objects.all()
    serializer = ProductSerializer(new, many=True)
    search_by = request.query_params.get("search_by", "")  # query params
    news_objs = models.Product.objects.filter(author__icontains=search_by)  # DB -> Python
    news_jsons = serializers.ProductSerializer(news_objs, many=True).data  # Python -> JSON

    combined_data = {
        "products": serializer.data,
        "search_results": news_jsons
    }

    return Response(combined_data, status=status.HTTP_200_OK)




@swagger_auto_schema(
    method="POST",
    request_body=serializers.ProductSerializer,  # Описание входных данных
    responses={201: "Успех", 400: "Error detail"},  # Описание выходных данных
)
@api_view(http_method_names=["POST"])
def addproduct(request):
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    return Response(serializer.data)





@api_view(http_method_names=["GET", "PUT", "DELETE"])
def product_id(request: Request, pk: str) -> Response:
    if request.method == "GET":
        return Response(data=serializers.ProductSerializer(models.Product.objects.get(id=int(pk)), many=False).data, status=status.HTTP_200_OK)
    elif request.method == "PUT":

        product_id = models.Product.objects.get(id=int(pk))
        article = str(request.data.get('article', ''))
        if len(article) > 0:
            product_id.article = article

        name = str(request.data.get('name', ''))
        if len(name) > 0:
            product_id.name = name

        price = str(request.data.get('price', ''))
        if len(price) > 0:
            product_id.price = price

        quantity_in_stock = str(request.data.get('quantity_in_stock', ''))
        if len(quantity_in_stock) > 0:
            product_id.description = quantity_in_stock

        quantity_on_hand = str(request.data.get('quantity_on_hand', ''))
        if len(quantity_on_hand) > 0:
            product_id.quantity_on_hand = quantity_on_hand

        product_id.save()

        return Response(data={"message": "successfully updated."}, status=status.HTTP_200_OK)
    elif request.method == "DELETE":
        models.Product.objects.get(id=int(pk)).delete()
        return Response(data={"message": "successfully deleted."}, status=status.HTTP_200_OK)
    else:
        return Response(data={"message": "HTTP_405_METHOD_NOT_ALLOWED"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

#TODO CELERY+REDIS and SENDING PDF
def celer(request):


    """
    # ssh
    sudo apt-get update -y
    sudo apt-get install -y openssh-server
    sudo systemctl start ssh
    sudo systemctl restart ssh
    ip a
    # ssh

    # redis
    sudo apt update -y
    sudo apt install -y redis
    redis-server
    redis-cli
    ping # PONG
    exit
    # redis


    # python
    python3.11 -V
    sudo apt-get update -y
    sudo apt-get install -y wget
    sudo apt-get install -y build-essential libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt-get install -y python3.11 python3.11-venv python3.11-dev
    python3.11 -V
    # python

    # web
    cd ~/Downloads/web
    python3.11 -m venv env
    source env/bin/activate
    python -V
    pip install celery django-redis
    pip install -r requirements.txt
    python manage.py runserver 0.0.0.0:8000
    http://127.0.0.1:8000/celer/
    # web

    # celery
    python -m celery -A django_settings worker -l info
    # celery

    """

    #

    # task_id = django_app_celery.add(random.randint(1, 10), random.randint(1, 10))  # прямой вызов
    # task_id = django_app_celery.add.apply_async((random.randint(1, 10), random.randint(1, 10)))  # *ARGS
    # print(task_id)
    #
    # # c6f55087-2769-4df4-8945-244693faa416

    # TODO GET RESULT FROM CELERY
    task_id = "ed8a9aa0-6cee-4b89-8161-be55560c66fa"
    result = AsyncResult(task_id, app=current_celery_app)
    if result.state == "SUCCESS":
        res = f"{result.state} {result.get()}"
    else:
        res = f"{result.state} {None}"

    return HttpResponse(f"<h1>Task_id: {task_id} [{res}]</h1>")

def start(request):

    # TODO START CELERY TASK
    task_id = django_app_celery.schedule_generate_and_email_pdf.apply_async()
    return HttpResponse(f"<h1>Task_id: {task_id}</h1>")






