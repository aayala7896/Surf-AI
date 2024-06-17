"""
URL configuration for surfai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from api import views as api_views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', api_views.home,name="home"),
    path('upload/', api_views.upload, name="upload"),
    path('join/', api_views.join, name="join"),
    path('surfVisual/', api_views.surfVisual, name="surfVisual"),
    path('login/', api_views.user_login, name="login"),
    path('userHome/', api_views.userhome, name="userHome"),
    path('process_video/', api_views.process_video, name="process_video"),
    path('logout/', api_views.log_out, name="log_out"),
    path('settings/',api_views.settings,name = "settings"),
    path('oauth/authorize',api_views.auth,name = "authorize"),
    path('update_reel_name/', api_views.update_reel_name, name="update_reel_name")
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
