from django.urls import re_path
from . import views


urlpatterns = [
    re_path(r'^$', views.RestCaptchaView.as_view(), name='rest_captcha'),
]
