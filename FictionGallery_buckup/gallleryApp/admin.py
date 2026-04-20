from django.contrib import admin
from gallleryApp.models import Profile, Genres,Novels,Review,Status

# Register your models here.
admin.site.register(Profile)
admin.site.register(Genres)
admin.site.register(Novels)
admin.site.register(Review)
admin.site.register(Status)