from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Employee, ExposureFactor, Referral, ReferralTemplate, User


class HRUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = (
            'first_name',
            'last_name',
            'pesel',
            'birth_date',
            'identity_document',
            'email',
            'phone',
            'city',
            'street',
            'building_number',
            'apartment_number',
            'job_position',
            'active',
        )
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }


class EmployeeImportForm(forms.Form):
    file = forms.FileField(label='Plik XLSX')


class ExposureFactorForm(forms.ModelForm):
    class Meta:
        model = ExposureFactor
        fields = ('category', 'name')


class ReferralForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=ReferralTemplate.objects.none(),
        required=False,
        label='Szablon stanowiska',
    )
    save_as_template = forms.BooleanField(required=False, label='Zapisz jako szablon')
    template_name = forms.CharField(required=False, label='Nazwa szablonu')

    class Meta:
        model = Referral
        fields = (
            'employee',
            'examination_type',
            'job_position',
            'work_description',
            'deadline',
        )
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, organization, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee'].queryset = Employee.objects.filter(
            organization=organization,
            active=True,
        ).order_by('last_name', 'first_name')
        self.fields['template'].queryset = ReferralTemplate.objects.filter(
            organization=organization,
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('save_as_template') and not cleaned_data.get('template_name'):
            self.add_error('template_name', 'Podaj nazwe szablonu.')
        return cleaned_data
