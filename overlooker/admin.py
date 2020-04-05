from django.contrib import admin

from constants import AdminSite

admin.site.site_header = AdminSite.HEADER
admin.site.site_title = AdminSite.TITLE