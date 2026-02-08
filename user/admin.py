from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Chama, ChamaMember

@admin.register(Chama)
class ChamaAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']

@admin.register(ChamaMember)
class ChamaMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'chama', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'chama__name']
