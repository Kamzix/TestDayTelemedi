"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from occupational_health.views import (
    create_hr_user,
    delete_hr_user,
    employee_create,
    employee_delete,
    employee_edit,
    employee_import,
    employee_list,
    exposure_factor_create,
    exposure_factor_delete,
    exposure_factor_list,
    home,
    hr_user_list,
    referral_create,
    referral_detail,
    referral_list,
    referral_pdf,
    referral_status_update,
    referral_template_list,
)

urlpatterns = [
    path('', home, name='home'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', hr_user_list, name='hr_user_list'),
    path('users/create/', create_hr_user, name='create_hr_user'),
    path('users/<int:pk>/delete/', delete_hr_user, name='delete_hr_user'),
    path('employees/', employee_list, name='employee_list'),
    path('employees/create/', employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', employee_delete, name='employee_delete'),
    path('employees/import/', employee_import, name='employee_import'),
    path('exposure-factors/', exposure_factor_list, name='exposure_factor_list'),
    path('exposure-factors/create/', exposure_factor_create, name='exposure_factor_create'),
    path(
        'exposure-factors/<int:pk>/delete/',
        exposure_factor_delete,
        name='exposure_factor_delete',
    ),
    path('referrals/', referral_list, name='referral_list'),
    path('referrals/create/', referral_create, name='referral_create'),
    path('referrals/<int:pk>/pdf/', referral_pdf, name='referral_pdf'),
    path('referrals/<int:pk>/status/', referral_status_update, name='referral_status_update'),
    path('referrals/<int:pk>/', referral_detail, name='referral_detail'),
    path('referral-templates/', referral_template_list, name='referral_template_list'),
    path('admin/', admin.site.urls),
]
