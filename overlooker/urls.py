"""overlooker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path, include
from django.http import HttpResponseRedirect
from django.conf.urls import url
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from constants import OpenAPIInfo

schema_view = get_schema_view(
    openapi.Info(
        title=OpenAPIInfo.TITLE,
        default_version=OpenAPIInfo.VERSION,
        description=OpenAPIInfo.DESCRIPTION,
        terms_of_service=OpenAPIInfo.TERMS_OF_SERVICE,
        contact=openapi.Contact(email=OpenAPIInfo.CONTACT_EMAIL),
        license=openapi.License(name=OpenAPIInfo.LICENSE_NAME),
    ),
    public=True,
    # TODO: apenas admins deveriam acessar isso em produção
    permission_classes=(permissions.AllowAny,),
)

swagger_urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc')
]

# TODO: add djoser when user and auth is needed
djoser_urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path('', include('djoser.urls.jwt')),
    # path('', include('djoser.social.urls')),
]

urlpatterns = [
    *swagger_urlpatterns,
    *djoser_urlpatterns,
    path('admin/', admin.site.urls),
    path('', include('apps.scholar.urls')),
    path('', include('apps.agent.urls')),
]
