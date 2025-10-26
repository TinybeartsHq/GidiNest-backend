from django.contrib import admin

# Register your models here.

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("Clars Admin Panel")
admin.site.site_title = _("Clars")
admin.site.index_title = _("Welcome to Clars Admin Panel")