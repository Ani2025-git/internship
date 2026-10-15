"""
Django admin configuration for Factory Operations & Quality Control System.
Allows easy inspection and management of all models in the Django admin portal.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, ProductionJob, Inspection, DefectPhoto, ProcessHold, QualityCertificate

# Custom Admin Branding
admin.site.site_header = "QualiTrack Administration"
admin.site.site_title = "QualiTrack QC Portal"
admin.site.index_title = "Factory Quality & Dispatch Management"


# Inline UserProfile in Django's User Admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Role Profile'


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')

    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'Factory Role'


# Re-register User with customized admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Defect Photo Inline inside Inspection Admin
class DefectPhotoInline(admin.TabularInline):
    model = DefectPhoto
    extra = 1


@admin.register(ProductionJob)
class ProductionJobAdmin(admin.ModelAdmin):
    list_display = ('job_number', 'product_name', 'target_quantity', 'dispatch_status', 'cleared_by', 'created_at')
    list_filter = ('dispatch_status', 'created_at')
    search_fields = ('job_number', 'product_name')


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'job', 'inspector', 'measurement', 'min_limit', 'max_limit',
        'calculated_result', 'status', 'supervisor', 'created_at'
    )
    list_filter = ('calculated_result', 'status', 'created_at')
    search_fields = ('job__job_number', 'job__product_name', 'inspector__username')
    inlines = [DefectPhotoInline]


@admin.register(DefectPhoto)
class DefectPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'inspection', 'image', 'uploaded_at')


@admin.register(ProcessHold)
class ProcessHoldAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'reason', 'is_active', 'placed_by', 'placed_at', 'released_by', 'released_at')
    list_filter = ('is_active', 'placed_at')
    search_fields = ('job__job_number', 'reason')


@admin.register(QualityCertificate)
class QualityCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'certificate_number', 'job', 'is_dispatch_authorized', 'first_pass_yield',
        'inspected_units_count', 'inspected_dimensions_count', 'generated_by', 'generated_at'
    )
    list_filter = ('is_dispatch_authorized', 'generated_at')
    search_fields = ('certificate_number', 'job__job_number', 'sha256_hash')
    readonly_fields = ('certificate_number', 'generated_at', 'sha256_hash')

