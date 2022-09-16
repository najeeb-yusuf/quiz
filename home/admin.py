from django.contrib import admin
from . models import Question,Option,Section,Response
# Register your models here.

admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Section)

admin.site.register(Response)
