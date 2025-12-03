from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.index, name='index'),
    path("register", views.register_view, name="register"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),

    #API (JSON)
    path("api/conversations/", api.conversations_view, name="conversations"),
    path("api/conversations/<uuid:conversation_id>/messages/", api.messages_view, name="messages"),
    path("api/conversations/<uuid:conversation_id>/autodestruct/", api.autodestruct_view, name="autodestruct"),

]