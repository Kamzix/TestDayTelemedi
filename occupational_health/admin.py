from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Employee,
    ExposureFactor,
    Organization,
    Referral,
    ReferralExposure,
    ReferralTemplate,
    ReferralTemplateExposure,
    User,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'tax_id')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Organization and role', {'fields': ('organization', 'role')}),
    )
    list_display = ('username', 'email', 'organization', 'role', 'is_staff')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'organization', 'job_position', 'active')
    list_filter = ('organization', 'active')
    search_fields = ('first_name', 'last_name', 'pesel', 'email')


@admin.register(ExposureFactor)
class ExposureFactorAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_default', 'organization')
    list_filter = ('category', 'is_default', 'organization')
    search_fields = ('name',)


class ReferralExposureInline(admin.TabularInline):
    model = ReferralExposure
    extra = 0


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('employee', 'examination_type', 'job_position', 'deadline', 'status')
    list_filter = ('organization', 'examination_type', 'status')
    inlines = [ReferralExposureInline]


class ReferralTemplateExposureInline(admin.TabularInline):
    model = ReferralTemplateExposure
    extra = 0


@admin.register(ReferralTemplate)
class ReferralTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'job_position')
    list_filter = ('organization',)
    inlines = [ReferralTemplateExposureInline]
