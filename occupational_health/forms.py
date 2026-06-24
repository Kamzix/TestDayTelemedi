from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils import timezone

from .models import Employee, ExposureFactor, Referral, ReferralTemplate, User

MAX_IMPORT_FILE_SIZE = 2 * 1024 * 1024


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
            'first_name': forms.TextInput(attrs={'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'autocomplete': 'family-name'}),
            'pesel': forms.TextInput(attrs={'inputmode': 'numeric', 'maxlength': '11'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'identity_document': forms.TextInput(attrs={'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel', 'inputmode': 'tel'}),
            'city': forms.TextInput(attrs={'autocomplete': 'address-level2'}),
            'street': forms.TextInput(attrs={'autocomplete': 'address-line1'}),
        }


class EmployeeImportForm(forms.Form):
    file = forms.FileField(label='Plik XLSX')

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > MAX_IMPORT_FILE_SIZE:
            raise forms.ValidationError('Plik XLSX moze miec maksymalnie 2 MB.')
        if not file.name.lower().endswith('.xlsx'):
            raise forms.ValidationError('Wybierz plik w formacie .xlsx.')
        return file


class ExposureFactorForm(forms.ModelForm):
    class Meta:
        model = ExposureFactor
        fields = ('category', 'name')
        widgets = {
            'name': forms.TextInput(attrs={'maxlength': '200'}),
        }

    def __init__(self, *args, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.organization = organization

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if not name:
            raise forms.ValidationError('Nazwa czynnika jest wymagana.')
        return name

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        name = cleaned_data.get('name')
        if self.organization and category and name:
            exists = ExposureFactor.objects.filter(
                category=category,
                name__iexact=name,
                organization=self.organization,
                is_default=False,
            ).exists()
            if exists:
                self.add_error('name', 'Taki czynnik juz istnieje w tej kategorii.')
        return cleaned_data


class ReferralForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=ReferralTemplate.objects.none(),
        required=False,
        label='Szablon stanowiska',
    )
    save_as_template = forms.BooleanField(required=False, label='Zapisz jako szablon')
    template_name = forms.CharField(
        required=False,
        label='Nazwa szablonu',
        max_length=150,
        widget=forms.TextInput(attrs={'maxlength': '150'}),
    )

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
            'job_position': forms.TextInput(attrs={'maxlength': '150'}),
            'work_description': forms.Textarea(attrs={'maxlength': '3000', 'rows': '5'}),
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

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError('Termin badan nie moze byc w przeszlosci.')
        return deadline


class ReferralStatusForm(forms.Form):
    status = forms.ChoiceField(choices=Referral.Status.choices)
