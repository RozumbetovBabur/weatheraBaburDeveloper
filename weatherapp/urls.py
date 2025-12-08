# weatherapp/urls.py
from django.urls import path
from .views import home_page, RegisterView, LoginView, RegionsLotView, CityListView, WeatherView, token_login_page, dashboard_view, profile_details, profile_update, user_logout

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("", home_page, name="home"),
    path('auth/register', RegisterView.as_view(), name='register'),
    path('auth/login', LoginView.as_view(), name='login'),
    path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/city', CityListView.as_view(), name='city_list'),
    path('weather', WeatherView.as_view(), name='weather'),
    path('api/regions-lot/', RegionsLotView.as_view(), name='regions_lot'),
    path('auth/token-login', token_login_page, name='token_login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path("api/profile/", profile_details, name="profil_del"),
    path("api/profile/update/", profile_update, name="profile_update"),
    path('logout/', user_logout, name='logout'),

]
