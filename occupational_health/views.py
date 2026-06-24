from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .forms import (
    EmployeeForm,
    EmployeeImportForm,
    ExposureFactorForm,
    HRUserCreationForm,
    ReferralForm,
    ReferralStatusForm,
)
from .models import (
    Employee,
    ExposureFactor,
    Referral,
    ReferralExposure,
    ReferralTemplate,
    ReferralTemplateExposure,
    User,
)
from .services.employee_import import import_employees_from_xlsx
from .services.referral_pdf import generate_referral_pdf


def role_required(*allowed_roles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


@login_required
def home(request):
    return render(request, 'occupational_health/dashboard.html')


@role_required(User.Role.MANAGER)
def hr_user_list(request):
    users = User.objects.filter(
        organization=request.user.organization,
        role=User.Role.HR,
    ).order_by('last_name', 'first_name', 'username')
    return render(request, 'occupational_health/hr_user_list.html', {
        'users': users,
    })


@role_required(User.Role.MANAGER)
def create_hr_user(request):
    if request.method == 'POST':
        form = HRUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.organization = request.user.organization
            user.role = User.Role.HR
            user.save()
            messages.success(request, 'Utworzono konto HR.')
            return redirect('hr_user_list')
    else:
        form = HRUserCreationForm()

    return render(request, 'occupational_health/create_hr_user.html', {'form': form})


@role_required(User.Role.HR)
def employee_list(request):
    employees = Employee.objects.filter(
        organization=request.user.organization,
    ).order_by('last_name', 'first_name')
    return render(request, 'occupational_health/employee_list.html', {
        'employees': employees,
    })


@role_required(User.Role.HR)
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.organization = request.user.organization
            employee.save()
            messages.success(request, 'Utworzono pracownika.')
            return redirect('employee_list')
    else:
        form = EmployeeForm()

    return render(request, 'occupational_health/employee_form.html', {
        'form': form,
        'title': 'Dodaj pracownika',
    })


@role_required(User.Role.HR)
def employee_edit(request, pk):
    employee = get_object_or_404(
        Employee,
        pk=pk,
        organization=request.user.organization,
    )

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.organization = request.user.organization
            employee.save()
            messages.success(request, 'Zapisano zmiany pracownika.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'occupational_health/employee_form.html', {
        'form': form,
        'title': 'Edytuj pracownika',
    })


@role_required(User.Role.HR)
@require_POST
def employee_delete(request, pk):
    employee = get_object_or_404(
        Employee,
        pk=pk,
        organization=request.user.organization,
    )
    employee_name = f'{employee.first_name} {employee.last_name}'

    try:
        employee.delete()
    except ProtectedError:
        messages.error(request, 'Nie mo\u017cna usun\u0105\u0107 pracownika, kt\u00f3ry ma skierowania.')
    else:
        messages.success(request, f'Usuni\u0119to pracownika: {employee_name}.')

    return redirect('employee_list')


@role_required(User.Role.HR)
def employee_import(request):
    result = None
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
        if form.is_valid():
            result = import_employees_from_xlsx(
                form.cleaned_data['file'],
                request.user.organization,
            )
            messages.success(request, f'Import zakończony. Utworzono rekordy: {result.created_count}.')
    else:
        form = EmployeeImportForm()

    return render(request, 'occupational_health/employee_import.html', {
        'form': form,
        'result': result,
    })


@role_required(User.Role.HR)
def exposure_factor_list(request):
    factors = ExposureFactor.objects.filter(
        Q(is_default=True, organization__isnull=True) | Q(organization=request.user.organization),
    )
    grouped_factors = []
    for category_value, category_label in ExposureFactor.Category.choices:
        grouped_factors.append((
            category_label,
            [factor for factor in factors if factor.category == category_value],
        ))

    return render(request, 'occupational_health/exposure_factor_list.html', {
        'grouped_factors': grouped_factors,
    })


@role_required(User.Role.HR)
def exposure_factor_create(request):
    if request.method == 'POST':
        form = ExposureFactorForm(request.POST, organization=request.user.organization)
        if form.is_valid():
            factor = form.save(commit=False)
            factor.is_default = False
            factor.organization = request.user.organization
            factor.created_by = request.user
            factor.save()
            messages.success(request, 'Dodano własny czynnik narażenia.')
            return redirect('exposure_factor_list')
    else:
        form = ExposureFactorForm(organization=request.user.organization)

    return render(request, 'occupational_health/exposure_factor_form.html', {
        'form': form,
    })


@role_required(User.Role.HR)
@require_POST
def exposure_factor_delete(request, pk):
    factor = get_object_or_404(
        ExposureFactor,
        pk=pk,
        is_default=False,
        organization=request.user.organization,
    )
    factor.delete()
    messages.success(request, 'Usunięto własny czynnik narażenia.')
    return redirect('exposure_factor_list')


@role_required(User.Role.HR)
def referral_list(request):
    referrals = Referral.objects.filter(
        organization=request.user.organization,
    ).select_related('employee', 'created_by')
    return render(request, 'occupational_health/referral_list.html', {
        'referrals': referrals,
        'status_choices': Referral.Status.choices,
    })


@role_required(User.Role.HR)
def referral_detail(request, pk):
    referral = get_object_or_404(
        Referral.objects.select_related('employee', 'created_by').prefetch_related(
            'exposures__exposure_factor',
        ),
        pk=pk,
        organization=request.user.organization,
    )
    return render(request, 'occupational_health/referral_detail.html', {
        'referral': referral,
        'status_choices': Referral.Status.choices,
    })


@role_required(User.Role.HR)
def referral_pdf(request, pk):
    referral = get_object_or_404(
        Referral.objects.select_related(
            'organization',
            'employee',
            'created_by',
        ).prefetch_related('exposures__exposure_factor'),
        pk=pk,
        organization=request.user.organization,
    )
    pdf_bytes = generate_referral_pdf(referral)
    employee_slug = slugify(referral.employee.last_name) or 'pracownik'
    filename = f'skierowanie-{referral.pk}-{employee_slug}.pdf'
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@role_required(User.Role.HR)
@require_POST
def referral_status_update(request, pk):
    referral = get_object_or_404(
        Referral,
        pk=pk,
        organization=request.user.organization,
    )
    form = ReferralStatusForm(request.POST)
    if form.is_valid():
        referral.status = form.cleaned_data['status']
        referral.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Zmieniono status skierowania.')
    return redirect('referral_detail', pk=referral.pk)


@role_required(User.Role.HR)
def referral_create(request):
    organization = request.user.organization
    template = _get_template_from_query(request, organization)
    available_factors = _available_exposure_factors(organization)

    if request.method == 'POST':
        form = ReferralForm(request.POST, organization=organization)
        selected_exposures, exposure_errors = _parse_exposure_post(
            request.POST,
            available_factors,
        )
        if exposure_errors:
            for error in exposure_errors:
                form.add_error(None, error)

        if form.is_valid() and not exposure_errors:
            with transaction.atomic():
                referral = form.save(commit=False)
                referral.organization = organization
                referral.created_by = request.user
                referral.status = Referral.Status.TO_ORDER
                referral.save()
                _save_referral_exposures(referral, selected_exposures)

                if form.cleaned_data['save_as_template']:
                    referral_template = ReferralTemplate.objects.create(
                        organization=organization,
                        name=form.cleaned_data['template_name'],
                        job_position=referral.job_position,
                        work_description=referral.work_description,
                        created_by=request.user,
                    )
                    _save_template_exposures(referral_template, selected_exposures)
                    messages.success(request, 'Utworzono skierowanie i zapisano szablon stanowiska.')
                else:
                    messages.success(request, 'Utworzono skierowanie.')

            return redirect('referral_detail', pk=referral.pk)
        exposure_data = _exposure_data_from_post(request.POST)
    else:
        initial = {}
        exposure_data = {}
        if template:
            initial = {
                'template': template,
                'job_position': template.job_position,
                'work_description': template.work_description,
            }
            exposure_data = _exposure_data_from_template(template)
        form = ReferralForm(initial=initial, organization=organization)

    return render(request, 'occupational_health/referral_form.html', {
        'form': form,
        'grouped_factor_rows': _group_factor_rows(available_factors, exposure_data),
    })


@role_required(User.Role.HR)
def referral_template_list(request):
    templates = ReferralTemplate.objects.filter(
        organization=request.user.organization,
    ).prefetch_related('exposures__exposure_factor')
    return render(request, 'occupational_health/referral_template_list.html', {
        'templates': templates,
    })


def _available_exposure_factors(organization):
    return ExposureFactor.objects.filter(
        Q(is_default=True, organization__isnull=True) | Q(organization=organization),
    ).order_by('category', 'name')


def _get_template_from_query(request, organization):
    template_id = request.GET.get('template')
    if not template_id:
        return None
    return get_object_or_404(
        ReferralTemplate.objects.prefetch_related('exposures__exposure_factor'),
        pk=template_id,
        organization=organization,
    )


def _parse_exposure_post(post_data, available_factors):
    allowed_factors = {str(factor.pk): factor for factor in available_factors}
    selected_ids = post_data.getlist('exposure_factors')
    selected_exposures = []
    errors = []

    if not selected_ids:
        return [], ['Wybierz minimum jeden czynnik narazenia.']

    seen_ids = set()
    for factor_id in selected_ids:
        if factor_id in seen_ids:
            continue
        seen_ids.add(factor_id)
        factor = allowed_factors.get(factor_id)
        if not factor:
            errors.append('Wybrano niedozwolony czynnik narazenia.')
            continue

        description = post_data.get(f'exposure_description_{factor_id}', '').strip()
        measurement = post_data.get(f'measurement_result_{factor_id}', '').strip()
        if not description:
            errors.append(f'Opis narazenia jest wymagany dla: {factor.name}.')
            continue
        if len(description) > 1000:
            errors.append(f'Opis narazenia jest za dlugi dla: {factor.name}.')
            continue
        if len(measurement) > 500:
            errors.append(f'Wynik pomiaru jest za dlugi dla: {factor.name}.')
            continue

        selected_exposures.append({
            'factor': factor,
            'description': description,
            'measurement': measurement,
        })

    return selected_exposures, errors


def _exposure_data_from_post(post_data):
    exposure_data = {}
    for factor_id in post_data.getlist('exposure_factors'):
        exposure_data[str(factor_id)] = {
            'selected': True,
            'description': post_data.get(f'exposure_description_{factor_id}', ''),
            'measurement': post_data.get(f'measurement_result_{factor_id}', ''),
        }
    return exposure_data


def _exposure_data_from_template(template):
    return {
        str(exposure.exposure_factor_id): {
            'selected': True,
            'description': exposure.exposure_description,
            'measurement': exposure.measurement_result,
        }
        for exposure in template.exposures.all()
    }


def _group_factor_rows(factors, exposure_data):
    grouped_rows = []
    for category_value, category_label in ExposureFactor.Category.choices:
        rows = []
        for factor in factors:
            if factor.category != category_value:
                continue
            data = exposure_data.get(str(factor.pk), {})
            rows.append({
                'factor': factor,
                'selected': data.get('selected', False),
                'description': data.get('description', ''),
                'measurement': data.get('measurement', ''),
            })
        grouped_rows.append((category_label, rows))
    return grouped_rows


def _save_referral_exposures(referral, selected_exposures):
    for exposure in selected_exposures:
        ReferralExposure.objects.create(
            referral=referral,
            exposure_factor=exposure['factor'],
            exposure_description=exposure['description'],
            measurement_result=exposure['measurement'],
        )


def _save_template_exposures(referral_template, selected_exposures):
    for exposure in selected_exposures:
        ReferralTemplateExposure.objects.create(
            template=referral_template,
            exposure_factor=exposure['factor'],
            exposure_description=exposure['description'],
            measurement_result=exposure['measurement'],
        )
