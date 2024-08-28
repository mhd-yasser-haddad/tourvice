from django.urls import path
from account.api.views import (
    registration_view,
    CustomAuthToken
)
from account.api import views

app_name = "account"

urlpatterns = [
    path('register', registration_view, name="register"),
    path('login', CustomAuthToken.as_view(), name="login"),
    path('userImage', views.UserImageDetails.as_view(), name="UserImage"),
    path('userDocument', views.UserFileDetails.as_view(), name="UserDocument"),
]
