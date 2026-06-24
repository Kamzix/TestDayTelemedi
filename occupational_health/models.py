from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    tax_id = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGER = 'MANAGER', 'Manager'
        HR = 'HR', 'HR'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.HR)


class Employee(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='employees',
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    pesel = models.CharField(max_length=11, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    identity_document = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    building_number = models.CharField(max_length=20)
    apartment_number = models.CharField(max_length=20, blank=True)
    job_position = models.CharField(max_length=150)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}
        if self.pesel and (len(self.pesel) != 11 or not self.pesel.isdigit()):
            errors['pesel'] = 'PESEL musi skladac sie z dokladnie 11 cyfr.'
        if not self.pesel and (not self.birth_date or not self.identity_document):
            message = 'Podaj PESEL albo date urodzenia oraz dokument tozsamosci.'
            if not self.birth_date:
                errors['birth_date'] = message
            if not self.identity_document:
                errors['identity_document'] = message
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'{self.first_name} {self.last_name} - {self.job_position}'


class ExposureFactor(models.Model):
    class Category(models.TextChoices):
        PHYSICAL = 'PHYSICAL', 'Czynniki fizyczne'
        DUST = 'DUST', 'Pyly'
        CHEMICAL = 'CHEMICAL', 'Czynniki chemiczne'
        BIOLOGICAL = 'BIOLOGICAL', 'Czynniki biologiczne'
        OTHER = 'OTHER', 'Inne czynniki, w tym niebezpieczne i uciazliwe'

    category = models.CharField(max_length=20, choices=Category.choices)
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='exposure_factors',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='created_exposure_factors',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('category', 'name')

    def __str__(self):
        return f'{self.get_category_display()}: {self.name}'


class Referral(models.Model):
    class ExaminationType(models.TextChoices):
        INITIAL = 'INITIAL', 'Wstepne'
        PERIODIC = 'PERIODIC', 'Okresowe'
        CONTROL = 'CONTROL', 'Kontrolne'

    class Status(models.TextChoices):
        TO_ORDER = 'TO_ORDER', 'Do zlecenia'
        ORDERED = 'ORDERED', 'Zlecone'
        COMPLETED = 'COMPLETED', 'Wykonane'
        CANCELLED = 'CANCELLED', 'Anulowane'

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name='referrals',
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name='referrals',
    )
    examination_type = models.CharField(max_length=20, choices=ExaminationType.choices)
    job_position = models.CharField(max_length=150)
    work_description = models.TextField()
    deadline = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TO_ORDER,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_referrals',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    @property
    def is_overdue(self):
        return (
            self.deadline < timezone.localdate()
            and self.status not in {self.Status.COMPLETED, self.Status.CANCELLED}
        )

    def __str__(self):
        return f'{self.employee} - {self.get_examination_type_display()}'


class ReferralExposure(models.Model):
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name='exposures',
    )
    exposure_factor = models.ForeignKey(
        ExposureFactor,
        on_delete=models.PROTECT,
        related_name='referral_exposures',
    )
    exposure_description = models.TextField()
    measurement_result = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('referral', 'exposure_factor'),
                name='unique_referral_exposure_factor',
            ),
        ]

    def __str__(self):
        return f'{self.referral} - {self.exposure_factor}'


class ReferralTemplate(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='referral_templates',
    )
    name = models.CharField(max_length=255)
    job_position = models.CharField(max_length=150)
    work_description = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_referral_templates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class ReferralTemplateExposure(models.Model):
    template = models.ForeignKey(
        ReferralTemplate,
        on_delete=models.CASCADE,
        related_name='exposures',
    )
    exposure_factor = models.ForeignKey(
        ExposureFactor,
        on_delete=models.PROTECT,
        related_name='template_exposures',
    )
    exposure_description = models.TextField()
    measurement_result = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('template', 'exposure_factor'),
                name='unique_referral_template_exposure_factor',
            ),
        ]

    def __str__(self):
        return f'{self.template} - {self.exposure_factor}'
