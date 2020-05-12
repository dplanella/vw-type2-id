from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth import get_user_model


class CustomUserAdmin(UserAdmin):
    model = get_user_model()
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm


admin.site.register(get_user_model(), CustomUserAdmin)
