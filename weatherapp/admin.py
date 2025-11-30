# users/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin
from .models import User, WeatherCache
import json

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Location', {'fields': ('region', 'city')}),
    )
    list_display = ('username', 'email', 'region', 'city', 'is_staff', 'is_active')

@admin.register(WeatherCache)
class WeatherCacheAdmin(admin.ModelAdmin):
    list_display = ('city_key', 'short_summary', 'created_at')
    list_filter = ('created_at', 'city_key')
    search_fields = ('city_key',)
    readonly_fields = ('pretty_json', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25

    def short_summary(self, obj):
        """Qısqa kórinis: temperaturanı hám depscriptionni kórsetedi (eger ámeldegi bolsa)."""
        try:
            d = obj.data
            temp = d.get('main', {}).get('temp')
            desc = d.get('weather', [{}])[0].get('description')
            if temp is not None:
                t = f"{round(temp)}°C"
            else:
                t = "-"
            if desc:
                return f"{t} — {desc.capitalize()}"
            return t
        except Exception:
            return '-'
    short_summary.short_description = 'Hawa (qısqasha)'

    def pretty_json(self, obj):
        """JSON data ni chiroyli format qilib ko'rsatadi (readonly field)."""
        try:
            pretty = json.dumps(obj.data, ensure_ascii=False, indent=2)
            # <pre> bilan formatlash, HTML sahifada chiroyli koʻrsatadi
            return mark_safe('<pre style="white-space:pre-wrap; max-height:400px; overflow:auto;">{}</pre>'.format(
                pretty.replace('<', '&lt;').replace('>', '&gt;')
            ))
        except Exception as e:
            return str(obj.data)
    pretty_json.short_description = 'JSON malıwmatı (raw)'

    actions = ['clear_cache_older_than_one_hour']

    def clear_cache_older_than_one_hour(self, request, queryset):
        """
        Admin action: saylanǵan jazıwlardı óshiredi.
        (Yamasa kerek bolsa avtomatikalıq waqıt menen óshiriwdi jazıń)
        """
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} ta cache jazıwı óshirildi.")
    clear_cache_older_than_one_hour.short_description = 'Saylanǵan cache jazıwların óshiriw'
