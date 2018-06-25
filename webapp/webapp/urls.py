"""webapp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from webapp import views, utils

urlpatterns = [
    url(r'^$', views.main),
    url(r'^create', views.create),
    url(r'^manualcache', views.manualcache),
    url(r'^browse', views.browse),
    url(r'^search', views.search),
    url(r'^submit_from_browse/', views.submit_from_browse),
    url(r'^submit/', views.submit),
    url(r'^progress', utils.progress),
    url(r'^admin/', admin.site.urls),
    url(r'^autocomplete', views.autocomplete),
    url(r'^view_papers/', views.view_papers),
    url(r'^resubmit/', views.resubmit)
]
