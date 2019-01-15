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
from webapp import views

urlpatterns = [
    url(r'^$', views.main),
    url(r'^create', views.create),
    url(r'^curate_load_file', views.curate_load_file),
    url(r'^curate', views.curate),
    url(r'^check_record', views.check_record),
    url(r'^get_publication_papers', views.get_publication_papers),
    url(r'^get_citation_papers', views.get_citation_papers),
    url(r'^manualcache', views.manualcache),
    url(r'^browse', views.browse),
    url(r'^search', views.search),
    url(r'^submit/', views.submit),
    url(r'^admin/', admin.site.urls),
    url(r'^autocomplete', views.autocomplete),
    url(r'^resubmit/', views.resubmit),
    url(r'^get_node_info/', views.get_node_info),
    url(r'^get_next_node_info_page/', views.get_next_node_info_page),
    url(r'^redirect/', views.redirect)
]
