from django.urls import path
from django_app import views
from django_app import views_a
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import re_path



schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path("main/", views.home, name="home"),


    #TODO Аутентификация
    path("register/", views.register, name="register"),
    path("login/", views.login_f, name="login"),
    path("logout/", views.logout_, name="logout"),

    #TODO Домашняя страница
    path("home/", views.home_l, name="home_l"),

    #TODO CRUD IDEA
    path("createidea/", views.idea_create, name="idea_create"),
    path("list/", views.list_ideas, name="list_ideas"),
    path('detail/<str:pk>/', views.idea_detail, name="idea_detail"),
    path('delete/<str:pk>/', views.idea_delete, name="idea_delete"),
    path('idea/edit/<str:pk>/', views.idea_edit, name='idea_edit'),
    path("idea/comment/create/<str:pk>/", views.idea_comment_create, name="idea_comment_create"),
    path("idea/rating/<str:pk>/<str:is_like>/", views.idea_rating, name="idea_rating"),
    path("topideas/", views.display_top_ideas, name="display_top_idea"),

    #TODO CRUD вакансии
    path('vacancy/new/', views.vacancy_create, name='vacancy_create'),
    path('vacancy/', views.vacancy_list, name='vacancy_list'),
    path('vacancy/delete/<str:pk>/', views.vacancy_delete, name='vacancy_delete'),
    path('vacancy/detail/<str:pk>/', views.vacancy_detail, name='vacancy_detail'),
    path('vacancy/edit/<str:pk>/', views.vacancy_edit, name='vacancy_edit'),

    #TODO CRUD резюме
    path('resume/new/', views.resume_create, name='resume_create'),
    path('resume/', views.list_resumes, name='resume_list'),
    path('resume/delete/<str:pk>/', views.resume_delete, name='resume_delete'),
    path('resume/detail/<str:pk>/', views.resume_detail, name='resume_detail'),
    path('resume/edit/<str:pk>/', views.resume_edit, name='resume_edit'),
    path("resume/comment/create/<str:pk>/", views.resume_comment_create, name="resume_create_comment"),
    path("resume/rating/<str:pk>/<str:is_like>/", views.resume_rating, name="resume_rating"),

    #TODO DRF+SWAGGER
    path("api/swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path('post/', views.addproduct),
    path('product/', views.products),
    path('product/<str:pk>', views.product_id),

    #TODO КРИПТАА
    path('market/', views.get_coin, name='market'),

    #TODO CELERY
    path('celer/', views.celer, name="celer"),
    path('start/', views.start, name="start"),

    #TODO Онлайн-Чат
    path("onlinechat/", views.rooms, name="rooms"),
    path("<slug:slug>/", views.room, name="room"),






]
websocket_urlpatterns = [
    path('ws/<slug:room_name>/', views_a.ChatConsumer.as_asgi())
]
