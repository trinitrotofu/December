"""December URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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

from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings

from . import views

urlpatterns = [
    url(r'^install$', views.install_page),
    url(r'^login$', views.login_page),
    url(r'^logout$', views.logout_page),
    url(r'^$', views.index_page),
    url(r'^page/(?P<num>\d+)$', views.index_page),
    url(r'^admin$', views.admin_page),
    url(r'^admin/settings$', views.settings_page),
    url(r'^admin/media$', views.media_page),
    url(r'^admin/edit$', views.edit_page),
    url(r'^admin/edit/(?P<pid>\d+)$', views.edit_page),
    url(r'^admin/edit-comment/(?P<cid>\d+)$', views.edit_comment_page),
    url(r'^archives/(?P<pid>\d+)$', views.archives_page),
]

for url in settings.STATIC_DIC:
    urlpatterns += static(url, document_root=settings.STATIC_DIC[url])
