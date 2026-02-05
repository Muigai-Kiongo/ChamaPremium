from django.contrib import admin

# Register your models here.
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Channel, Request, Webinar, WebinarAttendance, ChannelMembership

User = get_user_model()

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_private', 'member_count', 'created_at']
    list_filter = ['is_private', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def member_count(self, obj):
        try:
            return obj.channelmembership_set.count()
        except Exception:
            return "?"
    member_count.short_description = 'Members'

@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'scheduled_at', 'status', 'attendee_count', 'meet_link_preview']
    list_filter = ['channel', 'status', 'scheduled_at']
    search_fields = ['title', 'description']
    
    readonly_fields = ['created_at', 'updated_at', 'attendee_count', 'created_by']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'channel', 'status', 'created_by')
        }),
        ('Schedule', {
            'fields': ('scheduled_at', 'duration_minutes', 'max_attendees')
        }),
        ('Google Meet', {
            'fields': ('google_meet_link',),
            'description': 'Use GENERATE button in form for auto-link!'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def attendee_count(self, obj):
        return obj.attendance.count()
    attendee_count.short_description = 'Attendees'
    
    def meet_link_preview(self, obj):
        if obj.google_meet_link:
            return format_html(
                '<a href="{}" target="_blank" class="btn btn-sm btn-outline-primary">'
                '<i class="fab fa-google-meet me-1"></i>Open Meet</a>',
                obj.google_meet_link
            )
        return 'No link'
    meet_link_preview.short_description = 'Meet Link'
    
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
   
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if 'created_by' in form.base_fields:
            form.base_fields['created_by'].widget.attrs['readonly'] = True
        return form
    change_form_template = 'admin/channels_app/webinar/changeform.html'

@admin.register(WebinarAttendance)
class WebinarAttendanceAdmin(admin.ModelAdmin):
    list_display = ['webinar', 'member', 'joined_at']
    list_filter = ['webinar__channel', 'joined_at']
    raw_id_fields = ['webinar', 'member']
    autocomplete_fields = ['webinar', 'member']

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'requester', 'status', 'amount_display', 'created_at']
    list_filter = ['channel', 'status', 'type', 'created_at']
    search_fields = ['title', 'description']
    
    readonly_fields = ['created_at', 'resolved_at', 'resolved_by']
    
    fieldsets = (
        ('Request Info', {
            'fields': ('channel', 'requester', 'type', 'title', 'description')
        }),
        ('Financial Details', {
            'fields': ('amount',),
            'classes': ('collapse',)
        }),
        ('Status & Resolution', {
            'fields': ('status', 'resolved_at', 'resolved_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        if obj.amount:
            return format_html('<strong class="text-success">KSh {:,.0f}</strong>', obj.amount)
        return '-'
    amount_display.short_description = 'Amount'
    
    # Admin actions
    actions = ['approve_requests', 'reject_requests']
    
    def approve_requests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='approved',
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} request(s) approved successfully', level='success')
    approve_requests.short_description = "Approve selected requests"
    approve_requests.action_name = 'approve_requests'
    
    def reject_requests(self, request, queryset):
        from django.utils import timezone
        updated = queryset.filter(status='pending').update(
            status='rejected',
            resolved_at=timezone.now(),
            resolved_by=request.user
        )
        self.message_user(request, f'{updated} request(s) rejected', level='warning')
    reject_requests.short_description = "Reject selected requests"
    reject_requests.action_name = 'reject_requests'

@admin.register(ChannelMembership)
class ChannelMembershipAdmin(admin.ModelAdmin):
    list_display = ['channel', 'user', 'joined_at', 'is_active']
    list_filter = ['channel', 'joined_at', 'is_active']
    raw_id_fields = ['channel', 'user']
    search_fields = ['user__username', 'channel__name']