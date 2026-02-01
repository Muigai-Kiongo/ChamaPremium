from django.contrib import admin

# Register your models here.
from .models import Meeting, LiveNote, AIConversation

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    """Chama meeting management"""
    list_display = ['name', 'chama_id', 'user', 'is_live', 'note_count', 'created_at']
    list_filter = ['is_live', 'created_at', 'user']
    search_fields = ['name', 'chama_id']
    readonly_fields = ['created_at']
    fieldsets = (
        ('Meeting Info', {
            'fields': ('name', 'chama_id', 'user', 'is_live')
        }),
        ('Status', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def note_count(self, obj):
        return obj.livenote_set.count()
    note_count.short_description = 'Live Notes'

@admin.register(LiveNote)
class LiveNoteAdmin(admin.ModelAdmin):
    """AI-generated live meeting notes"""
    list_display = ['speaker', 'meeting_link', 'note_type', 'content_preview', 'timestamp']
    list_filter = ['note_type', 'timestamp', 'meeting']
    date_hierarchy = 'timestamp'
    search_fields = ['speaker', 'content']
    readonly_fields = ['timestamp']
    list_select_related = ['meeting']
    
    fieldsets = (
        ('Note Details', {
            'fields': ('meeting', 'speaker', 'content', 'note_type')
        }),
        ('Metadata', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def meeting_link(self, obj):
        return f"Meeting #{obj.meeting.id}"
    meeting_link.short_description = 'Meeting'
    
    def content_preview(self, obj):
        return obj.content[:50] + "..."
    content_preview.short_description = 'Preview'

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    """AI chat conversations"""
    list_display = ['user', 'meeting_link', 'prompt_preview', 'response_preview', 'created_at']
    list_filter = ['created_at', 'meeting']
    search_fields = ['prompt', 'response']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    list_select_related = ['user', 'meeting']
    
    fieldsets = (
        ('AI Chat', {
            'fields': ('user', 'meeting', 'prompt', 'response')
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def meeting_link(self, obj):
        if obj.meeting:
            return f"#{obj.meeting.id}"
        return "General"
    meeting_link.short_description = 'Meeting'
    
    def prompt_preview(self, obj):
        return obj.prompt[:30] + "..." if len(obj.prompt) > 30 else obj.prompt
    prompt_preview.short_description = 'Prompt'
    
    def response_preview(self, obj):
        return obj.response[:30] + "..." if len(obj.response) > 30 else obj.response
    response_preview.short_description = 'AI Response'

# Custom admin site title
admin.site.site_header = "Chama Premium Admin"
admin.site.site_title = "Chama Premium"
admin.site.index_title = "Manage Chama Groups & AI Features"
