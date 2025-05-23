from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser, Subscription


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email',
                           'password')}),
        (_('Personal info'), {'fields': ('first_name',
                                         'last_name',
                                         'avatar'
                                         )}),
        (_('Permissions'), {'fields': ('is_active',
                                       'is_staff',
                                       'is_superuser',
                                       'groups',
                                       'user_permissions'
                                       )}),
        (_('Important dates'), {'fields': ('last_login',
                                           'date_joined'
                                           )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',
                       'username',
                       'first_name',
                       'last_name',
                       'password1',
                       'password2'),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    search_fields = ('user__email', 'author__email')
