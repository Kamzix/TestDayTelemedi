from io import BytesIO
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook

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


POLISH_TEXT = 'Zażółć gęślą jaźń ĄĆĘŁŃÓŚŹŻ ąćęłńóśźż'
MOJIBAKE_SEQUENCES = [
    ''.join(chr(codepoint) for codepoint in [0x0102, 0x2026, 0x00E2, 0x20AC, 0x0161]),
    ''.join(chr(codepoint) for codepoint in [0x0102, 0x201E, 0x00E2, 0x20AC, 0x00A6]),
    ''.join(chr(codepoint) for codepoint in [0x0102, 0x0083, 0x00C2, 0x0142]),
]


def make_employee_xlsx(rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append([
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
    ])
    for row in rows:
        sheet.append(row)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


class AccessAndOrganizationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Telemedi Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other Street 1',
            city='Warszawa',
            postal_code='00-001',
            tax_id='1111111111',
        )
        self.manager = User.objects.create_user(
            username='manager',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.MANAGER,
        )
        self.hr = User.objects.create_user(
            username='hr',
            password='Hr123456!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_hr = User.objects.create_user(
            username='other_hr',
            password='Hr123456!',
            organization=self.other_organization,
            role=User.Role.HR,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name='Anna',
            last_name='Nowak',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='1',
            job_position='Operator',
        )
        self.factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.PHYSICAL,
            name='Halas',
            is_default=True,
            organization=None,
        )
        self.referral = Referral.objects.create(
            organization=self.organization,
            employee=self.employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Operator',
            work_description='Praca przy maszynie',
            deadline=timezone.localdate() + timedelta(days=7),
            created_by=self.hr,
        )
        ReferralExposure.objects.create(
            referral=self.referral,
            exposure_factor=self.factor,
            exposure_description='Ekspozycja',
        )

    def test_anonymous_user_is_redirected_from_home_to_login(self):
        response = self.client.get(reverse('home'))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('home')}")

    def test_manager_can_open_hr_creation_form(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('create_hr_user'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Utwórz konto HR')

    def test_hr_gets_403_on_hr_creation_form(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('create_hr_user'))

        self.assertEqual(response.status_code, 403)

    def test_manager_creates_hr_in_own_organization(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('create_hr_user'), {
            'username': 'newhr',
            'first_name': 'New',
            'last_name': 'HR',
            'email': 'newhr@example.com',
            'password1': 'HrUser123!',
            'password2': 'HrUser123!',
        })

        self.assertRedirects(response, reverse('hr_user_list'))
        user = User.objects.get(username='newhr')
        self.assertEqual(user.organization, self.organization)
        self.assertEqual(user.role, User.Role.HR)

    def test_manager_cannot_assign_manager_role_by_post(self):
        self.client.force_login(self.manager)

        self.client.post(reverse('create_hr_user'), {
            'username': 'postedmanager',
            'first_name': 'Posted',
            'last_name': 'Manager',
            'email': 'postedmanager@example.com',
            'password1': 'HrUser123!',
            'password2': 'HrUser123!',
            'role': User.Role.MANAGER,
        })

        user = User.objects.get(username='postedmanager')
        self.assertEqual(user.role, User.Role.HR)

    def test_manager_cannot_assign_other_organization_by_post(self):
        self.client.force_login(self.manager)

        self.client.post(reverse('create_hr_user'), {
            'username': 'otherorghr',
            'first_name': 'Other',
            'last_name': 'Org',
            'email': 'otherorghr@example.com',
            'password1': 'HrUser123!',
            'password2': 'HrUser123!',
            'organization': self.other_organization.id,
        })

        user = User.objects.get(username='otherorghr')
        self.assertEqual(user.organization, self.organization)

    def test_created_hr_can_log_in(self):
        self.client.force_login(self.manager)
        self.client.post(reverse('create_hr_user'), {
            'username': 'loginhr',
            'first_name': 'Login',
            'last_name': 'HR',
            'email': 'loginhr@example.com',
            'password1': 'HrUser123!',
            'password2': 'HrUser123!',
        })
        self.client.logout()

        logged_in = self.client.login(username='loginhr', password='HrUser123!')

        self.assertTrue(logged_in)

    def test_hr_gets_403_on_hr_user_list(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('hr_user_list'))

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_employee_list(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('employee_list'))

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_employee_create(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('employee_create'))

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_employee_import(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('employee_import'))

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_employee_delete(self):
        self.client.force_login(self.manager)

        response = self.client.post(reverse('employee_delete', args=[self.employee.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Employee.objects.filter(pk=self.employee.pk).exists())

    def test_manager_gets_403_for_referral_create(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('referral_create'))

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_status_update(self):
        self.client.force_login(self.manager)

        response = self.client.post(
            reverse('referral_status_update', args=[self.referral.pk]),
            {'status': Referral.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 403)

    def test_manager_gets_403_for_referral_pdf(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('referral_pdf', args=[self.referral.pk]))

        self.assertEqual(response.status_code, 403)

    def test_manager_sees_only_hr_users_from_own_organization(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('hr_user_list'))
        users = list(response.context['users'])

        self.assertContains(response, self.hr.username)
        self.assertNotContains(response, self.other_hr.username)
        self.assertIn(self.hr, users)
        self.assertNotIn(self.other_hr, users)
        self.assertNotIn(self.manager, users)

    def test_manager_navigation_hides_hr_modules(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Konta HR')
        self.assertNotContains(response, 'Pracownicy')
        self.assertNotContains(response, 'Nowe skierowanie')
        self.assertNotContains(response, 'Skierowania')

    def test_hr_navigation_hides_user_management(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Pracownicy')
        self.assertNotContains(response, 'Konta HR')
        self.assertNotContains(response, 'Dodaj HR')

    def test_hr_can_use_full_operational_flow(self):
        self.client.force_login(self.hr)

        created_employee = self.client.post(reverse('employee_create'), {
            'first_name': 'Piotr',
            'last_name': 'Operacyjny',
            'pesel': '12345678901',
            'city': 'Warszawa',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Operator',
        })
        self.assertRedirects(created_employee, reverse('employee_list'))

        upload = SimpleUploadedFile(
            'employees.xlsx',
            make_employee_xlsx([[
                'Anna',
                'ImportFlow',
                '12345678901',
                '',
                '',
                '',
                '',
                'Warszawa',
                'Prosta',
                '2',
                '',
                'Technik',
                'tak',
            ]]),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        imported = self.client.post(reverse('employee_import'), {'file': upload})
        self.assertEqual(imported.status_code, 200)
        self.assertTrue(Employee.objects.filter(last_name='ImportFlow').exists())

        created_factor = self.client.post(reverse('exposure_factor_create'), {
            'category': ExposureFactor.Category.OTHER,
            'name': 'Czynnik flow',
        })
        self.assertRedirects(created_factor, reverse('exposure_factor_list'))
        own_factor = ExposureFactor.objects.get(name='Czynnik flow')

        created_referral = self.client.post(reverse('referral_create'), {
            'employee': self.employee.pk,
            'examination_type': Referral.ExaminationType.INITIAL,
            'job_position': 'Operator',
            'work_description': 'Praca operacyjna',
            'deadline': timezone.localdate() + timedelta(days=7),
            'save_as_template': 'on',
            'template_name': 'Szablon flow',
            'exposure_factors': [str(own_factor.pk)],
            f'exposure_description_{own_factor.pk}': 'Opis narażenia',
            f'measurement_result_{own_factor.pk}': 'brak',
        })
        referral = Referral.objects.exclude(pk=self.referral.pk).get()
        self.assertRedirects(created_referral, reverse('referral_detail', args=[referral.pk]))
        self.assertTrue(ReferralTemplate.objects.filter(name='Szablon flow').exists())

        status_response = self.client.post(
            reverse('referral_status_update', args=[referral.pk]),
            {'status': Referral.Status.ORDERED},
        )
        self.assertRedirects(status_response, reverse('referral_detail', args=[referral.pk]))
        referral.refresh_from_db()
        self.assertEqual(referral.status, Referral.Status.ORDERED)

        pdf_response = self.client.get(reverse('referral_pdf', args=[referral.pk]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertTrue(pdf_response.content.startswith(b'%PDF'))


class EmployeeTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Telemedi Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other Street 1',
            city='Krakow',
            postal_code='30-001',
            tax_id='1111111111',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_user = User.objects.create_user(
            username='otherhr',
            password='Manager123!',
            organization=self.other_organization,
            role=User.Role.HR,
        )

    def test_user_sees_only_employees_from_own_organization(self):
        own_employee = Employee.objects.create(
            organization=self.organization,
            first_name='Anna',
            last_name='Nowak',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='1',
            job_position='HR',
        )
        other_employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Manager',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('employee_list'))

        self.assertContains(response, own_employee.last_name)
        self.assertNotContains(response, other_employee.last_name)

    def test_user_gets_404_when_editing_employee_from_other_organization(self):
        employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Manager',
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('employee_edit', args=[employee.pk]))

        self.assertEqual(response.status_code, 404)

    def test_user_deletes_employee_from_own_organization(self):
        employee = Employee.objects.create(
            organization=self.organization,
            first_name='Adam',
            last_name='Kasprzak',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='3',
            job_position='Operator',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_delete', args=[employee.pk]))

        self.assertRedirects(response, reverse('employee_list'))
        self.assertFalse(Employee.objects.filter(pk=employee.pk).exists())

    def test_user_gets_404_when_deleting_employee_from_other_organization(self):
        employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Manager',
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_delete', args=[employee.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Employee.objects.filter(pk=employee.pk).exists())

    def test_employee_with_referral_is_not_deleted(self):
        employee = Employee.objects.create(
            organization=self.organization,
            first_name='Adam',
            last_name='Chroniony',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='3',
            job_position='Operator',
        )
        Referral.objects.create(
            organization=self.organization,
            employee=employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Operator',
            work_description='Praca przy maszynie',
            deadline=timezone.localdate() + timedelta(days=7),
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_delete', args=[employee.pk]))

        self.assertRedirects(response, reverse('employee_list'))
        self.assertTrue(Employee.objects.filter(pk=employee.pk).exists())

    def test_create_form_ignores_posted_organization(self):
        self.client.force_login(self.user)

        self.client.post(reverse('employee_create'), {
            'first_name': 'Maria',
            'last_name': 'Zielinska',
            'pesel': '12345678901',
            'city': 'Warszawa',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Specjalista',
            'organization': self.other_organization.id,
        })

        employee = Employee.objects.get(last_name='Zielinska')
        self.assertEqual(employee.organization, self.organization)

    def test_valid_employee_with_pesel_is_created(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_create'), {
            'first_name': 'Piotr',
            'last_name': 'Wisniewski',
            'pesel': '12345678901',
            'city': 'Warszawa',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Lekarz',
        })

        self.assertRedirects(response, reverse('employee_list'))
        self.assertTrue(Employee.objects.filter(last_name='Wisniewski').exists())

    def test_birth_date_and_identity_document_are_required_without_pesel(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_create'), {
            'first_name': 'Ewa',
            'last_name': 'Brakpesel',
            'city': 'Warszawa',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Analityk',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Employee.objects.filter(last_name='Brakpesel').exists())
        self.assertContains(response, 'Podaj PESEL albo date urodzenia oraz dokument tozsamosci')

    def test_valid_xlsx_row_is_imported_to_logged_user_organization(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            make_employee_xlsx([
                [
                    'Tomasz',
                    'Importowany',
                    '12345678901',
                    '',
                    '',
                    'tomasz@example.com',
                    '500600700',
                    'Warszawa',
                    'Prosta',
                    '1',
                    '',
                    'Technik',
                    'tak',
                ],
            ]),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        employee = Employee.objects.get(last_name='Importowany')
        self.assertEqual(employee.organization, self.organization)
        self.assertTrue(employee.active)

    def test_invalid_xlsx_row_is_reported_and_valid_row_is_saved(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            make_employee_xlsx([
                [
                    'Tomasz',
                    'Poprawny',
                    '12345678901',
                    '',
                    '',
                    '',
                    '',
                    'Warszawa',
                    'Prosta',
                    '1',
                    '',
                    'Technik',
                    'true',
                ],
                [
                    'Bledny',
                    'Wiersz',
                    '',
                    '',
                    '',
                    '',
                    '',
                    'Warszawa',
                    'Prosta',
                    '2',
                    '',
                    'Technik',
                    'true',
                ],
            ]),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Employee.objects.filter(last_name='Poprawny').exists())
        self.assertFalse(Employee.objects.filter(last_name='Wiersz').exists())
        self.assertContains(response, 'Wiersz 3')

    def test_non_xlsx_upload_is_rejected_before_import(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.txt',
            b'not an xlsx file',
            content_type='text/plain',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wybierz plik w formacie .xlsx')
        self.assertFalse(Employee.objects.filter(last_name='employees.txt').exists())

    def test_too_large_xlsx_upload_is_rejected_before_import(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            b'0' * (2 * 1024 * 1024 + 1),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Plik XLSX moze miec maksymalnie 2 MB')
        self.assertEqual(Employee.objects.count(), 0)

    def test_corrupted_xlsx_is_reported_without_creating_employees(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            b'corrupted workbook bytes',
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nie mozna odczytac pliku XLSX')
        self.assertEqual(Employee.objects.count(), 0)


class ExposureFactorTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Telemedi Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other Street 1',
            city='Krakow',
            postal_code='30-001',
            tax_id='1111111111',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_user = User.objects.create_user(
            username='otherhr',
            password='Manager123!',
            organization=self.other_organization,
            role=User.Role.HR,
        )
        self.default_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.PHYSICAL,
            name='Halas',
            is_default=True,
            organization=None,
        )
        self.own_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.CHEMICAL,
            name='Wlasny rozpuszczalnik',
            organization=self.organization,
            created_by=self.user,
        )
        self.other_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.BIOLOGICAL,
            name='Cudzy czynnik',
            organization=self.other_organization,
            created_by=self.other_user,
        )

    def test_user_sees_default_factors(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertContains(response, self.default_factor.name)

    def test_user_sees_own_factors(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertContains(response, self.own_factor.name)

    def test_user_does_not_see_other_organization_factors(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertNotContains(response, self.other_factor.name)

    def test_user_does_not_see_other_organization_factor_marked_default(self):
        ExposureFactor.objects.create(
            category=ExposureFactor.Category.OTHER,
            name='Bledny cudzy domyslny',
            is_default=True,
            organization=self.other_organization,
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertNotContains(response, 'Bledny cudzy domyslny')

    def test_create_ignores_posted_organization_is_default_and_created_by(self):
        self.client.force_login(self.user)

        self.client.post(reverse('exposure_factor_create'), {
            'category': ExposureFactor.Category.OTHER,
            'name': 'Nowy czynnik',
            'organization': self.other_organization.id,
            'is_default': 'on',
            'created_by': self.other_user.id,
        })

        factor = ExposureFactor.objects.get(name='Nowy czynnik')
        self.assertEqual(factor.organization, self.organization)
        self.assertFalse(factor.is_default)
        self.assertEqual(factor.created_by, self.user)

    def test_created_factor_belongs_to_logged_user_organization(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('exposure_factor_create'), {
            'category': ExposureFactor.Category.DUST,
            'name': 'Wlasny pyl',
        })

        self.assertRedirects(response, reverse('exposure_factor_list'))
        factor = ExposureFactor.objects.get(name='Wlasny pyl')
        self.assertEqual(factor.organization, self.organization)

    def test_default_factor_cannot_be_deleted(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('exposure_factor_delete', args=[self.default_factor.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ExposureFactor.objects.filter(pk=self.default_factor.pk).exists())

    def test_user_can_delete_own_factor(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('exposure_factor_delete', args=[self.own_factor.pk]))

        self.assertRedirects(response, reverse('exposure_factor_list'))
        self.assertFalse(ExposureFactor.objects.filter(pk=self.own_factor.pk).exists())

    def test_user_cannot_delete_other_organization_factor(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('exposure_factor_delete', args=[self.other_factor.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(ExposureFactor.objects.filter(pk=self.other_factor.pk).exists())

    def test_get_delete_does_not_delete_factor(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_delete', args=[self.own_factor.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(ExposureFactor.objects.filter(pk=self.own_factor.pk).exists())


class ReferralTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Telemedi Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other Street 1',
            city='Krakow',
            postal_code='30-001',
            tax_id='1111111111',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_user = User.objects.create_user(
            username='otherhr',
            password='Manager123!',
            organization=self.other_organization,
            role=User.Role.HR,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name='Anna',
            last_name='Nowak',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='1',
            job_position='Operator',
        )
        self.other_employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Technik',
        )
        self.default_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.PHYSICAL,
            name='Halas',
            is_default=True,
            organization=None,
        )
        self.own_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.CHEMICAL,
            name='Wlasny czynnik',
            organization=self.organization,
            created_by=self.user,
        )
        self.other_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.BIOLOGICAL,
            name='Cudzy czynnik',
            organization=self.other_organization,
            created_by=self.other_user,
        )

    def referral_payload(self, **overrides):
        data = {
            'employee': self.employee.pk,
            'examination_type': Referral.ExaminationType.INITIAL,
            'job_position': 'Operator',
            'work_description': 'Praca przy maszynie',
            'deadline': timezone.localdate() + timedelta(days=7),
            'exposure_factors': [str(self.default_factor.pk)],
            f'exposure_description_{self.default_factor.pk}': 'Ekspozycja codzienna',
            f'measurement_result_{self.default_factor.pk}': '80 dB',
        }
        data.update(overrides)
        return data

    def create_referral(self, organization=None, employee=None, user=None):
        organization = organization or self.organization
        employee = employee or self.employee
        user = user or self.user
        referral = Referral.objects.create(
            organization=organization,
            employee=employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Operator',
            work_description='Praca przy maszynie',
            deadline=timezone.localdate() + timedelta(days=7),
            created_by=user,
        )
        ReferralExposure.objects.create(
            referral=referral,
            exposure_factor=self.default_factor,
            exposure_description='Ekspozycja',
        )
        return referral

    def test_referral_list_shows_only_own_organization(self):
        own_referral = self.create_referral()
        other_referral = self.create_referral(
            organization=self.other_organization,
            employee=self.other_employee,
            user=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_list'))

        self.assertContains(response, own_referral.employee.last_name)
        self.assertNotContains(response, other_referral.employee.last_name)

    def test_other_organization_referral_detail_returns_404(self):
        referral = self.create_referral(
            organization=self.other_organization,
            employee=self.other_employee,
            user=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_detail', args=[referral.pk]))

        self.assertEqual(response.status_code, 404)

    def test_form_shows_only_own_organization_employees(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_create'))

        self.assertContains(response, self.employee.last_name)
        self.assertNotContains(response, self.other_employee.last_name)

    def test_form_shows_default_and_own_factors_but_not_other_factors(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_create'))

        self.assertContains(response, self.default_factor.name)
        self.assertContains(response, self.own_factor.name)
        self.assertNotContains(response, self.other_factor.name)

    def test_form_does_not_show_other_organization_factor_marked_default(self):
        ExposureFactor.objects.create(
            category=ExposureFactor.Category.OTHER,
            name='Bledny czynnik globalny',
            is_default=True,
            organization=self.other_organization,
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_create'))

        self.assertNotContains(response, 'Bledny czynnik globalny')

    def test_post_with_other_organization_employee_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            employee=self.other_employee.pk,
        ))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Referral.objects.exists())

    def test_post_with_other_organization_factor_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            exposure_factors=[str(self.other_factor.pk)],
            **{f'exposure_description_{self.other_factor.pk}': 'Cudza ekspozycja'},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Referral.objects.exists())
        self.assertContains(response, 'Wybrano niedozwolony czynnik narazenia')

    def test_valid_referral_saves_referral_and_exposures(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            exposure_factors=[str(self.default_factor.pk), str(self.own_factor.pk)],
            **{
                f'exposure_description_{self.own_factor.pk}': 'Kontakt tygodniowy',
                f'measurement_result_{self.own_factor.pk}': '',
            },
        ))

        referral = Referral.objects.get()
        self.assertRedirects(response, reverse('referral_detail', args=[referral.pk]))
        self.assertEqual(referral.exposures.count(), 2)
        self.assertEqual(referral.organization, self.organization)

    def test_referral_without_exposure_factors_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            exposure_factors=[],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Referral.objects.exists())
        self.assertContains(response, 'Wybierz minimum jeden czynnik narazenia')

    def test_selected_factor_without_description_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            **{f'exposure_description_{self.default_factor.pk}': ''},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Referral.objects.exists())
        self.assertContains(response, 'Opis narazenia jest wymagany')

    def test_organization_created_by_and_status_from_post_are_ignored(self):
        self.client.force_login(self.user)

        self.client.post(reverse('referral_create'), self.referral_payload(
            organization=self.other_organization.pk,
            created_by=self.other_user.pk,
            status=Referral.Status.COMPLETED,
        ))

        referral = Referral.objects.get()
        self.assertEqual(referral.organization, self.organization)
        self.assertEqual(referral.created_by, self.user)
        self.assertEqual(referral.status, Referral.Status.TO_ORDER)

    def test_save_as_template_creates_template_and_exposures(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            save_as_template='on',
            template_name='Operator maszyn',
            exposure_factors=[str(self.default_factor.pk), str(self.own_factor.pk)],
            **{
                f'exposure_description_{self.own_factor.pk}': 'Kontakt tygodniowy',
                f'measurement_result_{self.own_factor.pk}': 'brak',
            },
        ))

        self.assertEqual(response.status_code, 302)
        template = ReferralTemplate.objects.get(name='Operator maszyn')
        self.assertEqual(template.organization, self.organization)
        self.assertEqual(template.exposures.count(), 2)

    def test_other_organization_template_cannot_be_loaded(self):
        template = ReferralTemplate.objects.create(
            organization=self.other_organization,
            name='Cudzy szablon',
            job_position='Technik',
            work_description='Cudza praca',
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(f"{reverse('referral_create')}?template={template.pk}")

        self.assertEqual(response.status_code, 404)

    def test_own_template_prefills_initial_data(self):
        template = ReferralTemplate.objects.create(
            organization=self.organization,
            name='Wlasny szablon',
            job_position='Operator wzorcowy',
            work_description='Opis z szablonu',
            created_by=self.user,
        )
        ReferralTemplateExposure.objects.create(
            template=template,
            exposure_factor=self.default_factor,
            exposure_description='Opis czynnika z szablonu',
            measurement_result='82 dB',
        )
        self.client.force_login(self.user)

        response = self.client.get(f"{reverse('referral_create')}?template={template.pk}")

        self.assertContains(response, 'Operator wzorcowy')
        self.assertContains(response, 'Opis z szablonu')
        self.assertContains(response, 'Opis czynnika z szablonu')
        self.assertContains(response, '82 dB')

    def test_is_overdue_for_active_referral(self):
        referral = self.create_referral()
        referral.deadline = timezone.localdate() - timedelta(days=1)
        referral.save()

        self.assertTrue(referral.is_overdue)

    def test_completed_and_cancelled_referrals_are_not_overdue(self):
        completed = self.create_referral()
        completed.deadline = timezone.localdate() - timedelta(days=1)
        completed.status = Referral.Status.COMPLETED
        completed.save()
        cancelled = self.create_referral()
        cancelled.deadline = timezone.localdate() - timedelta(days=1)
        cancelled.status = Referral.Status.CANCELLED
        cancelled.save()

        self.assertFalse(completed.is_overdue)
        self.assertFalse(cancelled.is_overdue)


class ReferralPdfTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Zażółć Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other Street 1',
            city='Krakow',
            postal_code='30-001',
            tax_id='1111111111',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_user = User.objects.create_user(
            username='otherhr',
            password='Manager123!',
            organization=self.other_organization,
            role=User.Role.HR,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name='Łukasz',
            last_name='Żółć',
            pesel='12345678901',
            email='lukasz@example.com',
            phone='500600700',
            city='Łódź',
            street='Świętokrzyska',
            building_number='1',
            apartment_number='2',
            job_position='Operator',
        )
        self.employee_without_pesel = Employee.objects.create(
            organization=self.organization,
            first_name='Anna',
            last_name='Bezpesel',
            birth_date=timezone.localdate() - timedelta(days=10000),
            identity_document='ABC123456',
            city='Gdańsk',
            street='Długa',
            building_number='10',
            job_position='Technik',
        )
        self.other_employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Technik',
        )
        self.physical_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.PHYSICAL,
            name='Hałas',
            is_default=True,
            organization=None,
        )
        self.chemical_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.CHEMICAL,
            name='Środki dezynfekcyjne',
            is_default=True,
            organization=None,
        )
        self.biological_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.BIOLOGICAL,
            name='Bakterie i wirusy',
            is_default=True,
            organization=None,
        )

    def create_referral(self, employee=None, organization=None, created_by=None, factors=None):
        employee = employee or self.employee
        organization = organization or employee.organization
        created_by = created_by or self.user
        referral = Referral.objects.create(
            organization=organization,
            employee=employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Operator wózka',
            work_description='Praca w hałasie i kontakcie z czynnikami chemicznymi.',
            deadline=timezone.localdate() + timedelta(days=14),
            created_by=created_by,
        )
        for factor in factors or [self.physical_factor]:
            ReferralExposure.objects.create(
                referral=referral,
                exposure_factor=factor,
                exposure_description='Codzienna ekspozycja na czynnik.',
                measurement_result='80 dB' if factor == self.physical_factor else '',
            )
        return referral

    def test_valid_referral_pdf_returns_200(self):
        referral = self.create_referral()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 200)

    def test_referral_pdf_has_pdf_content_type(self):
        referral = self.create_referral()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_referral_pdf_starts_with_pdf_signature(self):
        referral = self.create_referral()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_user_cannot_download_other_organization_referral_pdf(self):
        referral = self.create_referral(
            employee=self.other_employee,
            organization=self.other_organization,
            created_by=self.other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_from_referral_pdf(self):
        referral = self.create_referral()

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('referral_pdf', args=[referral.pk])}",
        )

    def test_pdf_generates_for_employee_with_pesel(self):
        referral = self.create_referral(employee=self.employee)
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_generates_for_employee_without_pesel(self):
        referral = self.create_referral(employee=self.employee_without_pesel)
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_pdf_generates_with_polish_characters(self):
        referral = self.create_referral()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)

    def test_pdf_generates_with_many_factors_and_categories(self):
        referral = self.create_referral(
            factors=[
                self.physical_factor,
                self.chemical_factor,
                self.biological_factor,
            ],
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[referral.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertGreater(len(response.content), 0)


class ValidationStatusEncodingTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name=f'{POLISH_TEXT} Employer',
            address='Świętokrzyska 1',
            city='Łódź',
            postal_code='90-001',
            tax_id='1234567890',
        )
        self.other_organization = Organization.objects.create(
            name='Other Employer',
            address='Other 1',
            city='Krakow',
            postal_code='30-001',
            tax_id='9999999999',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.other_user = User.objects.create_user(
            username='otherhr',
            password='Manager123!',
            organization=self.other_organization,
            role=User.Role.HR,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name='Łukasz',
            last_name='Żółć',
            pesel='12345678901',
            city='Łódź',
            street='Świętokrzyska',
            building_number='1',
            job_position='Operator',
        )
        self.other_employee = Employee.objects.create(
            organization=self.other_organization,
            first_name='Jan',
            last_name='Kowalski',
            pesel='10987654321',
            city='Krakow',
            street='Dluga',
            building_number='2',
            job_position='Technik',
        )
        self.factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.PHYSICAL,
            name='Hałas',
            is_default=True,
            organization=None,
        )
        self.other_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.CHEMICAL,
            name='Cudzy czynnik',
            organization=self.other_organization,
            created_by=self.other_user,
        )
        self.referral = Referral.objects.create(
            organization=self.organization,
            employee=self.employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Operator',
            work_description='Opis pracy',
            deadline=timezone.localdate() + timedelta(days=7),
            created_by=self.user,
        )
        ReferralExposure.objects.create(
            referral=self.referral,
            exposure_factor=self.factor,
            exposure_description='Opis narażenia',
        )
        self.other_referral = Referral.objects.create(
            organization=self.other_organization,
            employee=self.other_employee,
            examination_type=Referral.ExaminationType.INITIAL,
            job_position='Technik',
            work_description='Cudzy opis',
            deadline=timezone.localdate() + timedelta(days=7),
            created_by=self.other_user,
        )

    def referral_payload(self, **overrides):
        data = {
            'employee': self.employee.pk,
            'examination_type': Referral.ExaminationType.INITIAL,
            'job_position': 'Operator',
            'work_description': 'Opis pracy',
            'deadline': timezone.localdate() + timedelta(days=7),
            'exposure_factors': [str(self.factor.pk)],
            f'exposure_description_{self.factor.pk}': 'Opis narażenia',
            f'measurement_result_{self.factor.pk}': '',
        }
        data.update(overrides)
        return data

    def test_own_referral_can_be_set_to_each_allowed_status(self):
        self.client.force_login(self.user)

        for status, _ in Referral.Status.choices:
            with self.subTest(status=status):
                response = self.client.post(
                    reverse('referral_status_update', args=[self.referral.pk]),
                    {'status': status},
                )
                self.referral.refresh_from_db()
                self.assertRedirects(response, reverse('referral_detail', args=[self.referral.pk]))
                self.assertEqual(self.referral.status, status)

    def test_invalid_status_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('referral_status_update', args=[self.referral.pk]),
            {'status': 'HACKED'},
        )

        self.referral.refresh_from_db()
        self.assertRedirects(response, reverse('referral_detail', args=[self.referral.pk]))
        self.assertEqual(self.referral.status, Referral.Status.TO_ORDER)

    def test_status_update_for_other_organization_returns_404(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('referral_status_update', args=[self.other_referral.pk]),
            {'status': Referral.Status.COMPLETED},
        )

        self.assertEqual(response.status_code, 404)

    def test_get_does_not_change_status(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_status_update', args=[self.referral.pk]))

        self.referral.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.referral.status, Referral.Status.TO_ORDER)

    def test_too_long_job_position_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            job_position='x' * 151,
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upewnij się, że ta wartość ma co najwyżej 150 znaków')

    def test_too_long_work_description_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            work_description='x' * 3001,
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Upewnij się, że ta wartość ma co najwyżej 3000 znaków')

    def test_too_long_exposure_description_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            **{f'exposure_description_{self.factor.pk}': 'x' * 1001},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Opis narazenia jest za dlugi')

    def test_invalid_pesel_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_create'), {
            'first_name': 'Bad',
            'last_name': 'Pesel',
            'pesel': '123',
            'city': 'Łódź',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Operator',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PESEL musi skladac sie z dokladnie 11 cyfr')

    def test_missing_pesel_and_identity_document_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('employee_create'), {
            'first_name': 'No',
            'last_name': 'Document',
            'city': 'Łódź',
            'street': 'Prosta',
            'building_number': '1',
            'job_position': 'Operator',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Podaj PESEL albo date urodzenia oraz dokument tozsamosci')

    def test_referral_without_factor_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            exposure_factors=[],
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wybierz minimum jeden czynnik narazenia')

    def test_referral_factor_without_description_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('referral_create'), self.referral_payload(
            **{f'exposure_description_{self.factor.pk}': ''},
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Opis narazenia jest wymagany')

    def test_invalid_status_from_create_post_is_ignored(self):
        self.client.force_login(self.user)

        self.client.post(reverse('referral_create'), self.referral_payload(status=Referral.Status.COMPLETED))

        created = Referral.objects.filter(
            organization=self.organization,
        ).exclude(pk=self.referral.pk).get()
        self.assertEqual(created.status, Referral.Status.TO_ORDER)

    def test_too_long_xlsx_data_is_reported_without_stopping_import(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            make_employee_xlsx([
                [
                    'Jan',
                    'Poprawny',
                    '12345678901',
                    '',
                    '',
                    '',
                    '',
                    'Łódź',
                    'Prosta',
                    '1',
                    '',
                    'Operator',
                    'tak',
                ],
                [
                    'A' * 101,
                    'ZaDlugi',
                    '12345678901',
                    '',
                    '',
                    '',
                    '',
                    'Łódź',
                    'Prosta',
                    '1',
                    '',
                    'Operator',
                    'tak',
                ],
            ]),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Employee.objects.filter(last_name='Poprawny').exists())
        self.assertFalse(Employee.objects.filter(last_name='ZaDlugi').exists())
        self.assertContains(response, 'Wiersz 3')

    def test_polish_characters_save_and_read_from_model(self):
        employee = Employee.objects.create(
            organization=self.organization,
            first_name='Zażółć',
            last_name='Gęślą',
            pesel='11111111111',
            city=POLISH_TEXT,
            street='Jaźń',
            building_number='3',
            job_position='Tester',
        )

        employee.refresh_from_db()
        self.assertEqual(employee.city, POLISH_TEXT)

    def test_polish_characters_render_in_html(self):
        self.employee.city = POLISH_TEXT
        self.employee.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('employee_list'))

        content = response.content.decode('utf-8')
        self.assertIn(POLISH_TEXT, content)
        self.assert_no_mojibake(content)

    def test_polish_characters_import_from_xlsx(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile(
            'employees.xlsx',
            make_employee_xlsx([
                [
                    'Zażółć',
                    'Gęślą',
                    '12345678901',
                    '',
                    '',
                    '',
                    '',
                    POLISH_TEXT,
                    'Świętokrzyska',
                    '1',
                    '',
                    'Łącznik',
                    'tak',
                ],
            ]),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

        response = self.client.post(reverse('employee_import'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        employee = Employee.objects.get(last_name='Gęślą')
        self.assertEqual(employee.city, POLISH_TEXT)

    def test_pdf_with_polish_characters_generates(self):
        self.organization.name = POLISH_TEXT
        self.organization.save()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_pdf', args=[self.referral.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))
        self.assertGreater(len(response.content), 0)

    def test_responses_do_not_contain_known_mojibake_sequences(self):
        self.client.force_login(self.user)

        responses = [
            self.client.get(reverse('employee_list')),
            self.client.get(reverse('referral_detail', args=[self.referral.pk])),
            self.client.get(reverse('referral_create')),
        ]

        for response in responses:
            self.assert_no_mojibake(response.content.decode('utf-8'))

    def assert_no_mojibake(self, text):
        for sequence in MOJIBAKE_SEQUENCES:
            self.assertNotIn(sequence, text)


class ExposureCatalogAndUiTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Telemedi Demo Employer',
            address='Rzymowskiego 53',
            city='Warszawa',
            postal_code='02-697',
            tax_id='0000000000',
        )
        self.user = User.objects.create_user(
            username='hr',
            password='Manager123!',
            organization=self.organization,
            role=User.Role.HR,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            first_name='Anna',
            last_name='Nowak',
            pesel='12345678901',
            city='Warszawa',
            street='Prosta',
            building_number='1',
            job_position='Operator',
        )

    def seed_catalog(self):
        call_command('seed_demo', verbosity=0)
        self.user.refresh_from_db()
        self.organization.refresh_from_db()

    def test_each_category_has_at_least_20_default_factors(self):
        self.seed_catalog()

        for category, _ in ExposureFactor.Category.choices:
            with self.subTest(category=category):
                self.assertGreaterEqual(
                    ExposureFactor.objects.filter(
                        is_default=True,
                        organization=None,
                        category=category,
                    ).count(),
                    20,
                )

    def test_default_catalog_has_at_least_100_factors(self):
        self.seed_catalog()

        self.assertGreaterEqual(
            ExposureFactor.objects.filter(is_default=True, organization=None).count(),
            100,
        )

    def test_repeated_seed_does_not_create_duplicates(self):
        self.seed_catalog()
        first_count = ExposureFactor.objects.filter(is_default=True, organization=None).count()

        self.seed_catalog()

        self.assertEqual(
            ExposureFactor.objects.filter(is_default=True, organization=None).count(),
            first_count,
        )

    def test_seed_creates_demo_hr_user(self):
        self.seed_catalog()

        hr_user = User.objects.get(username='hr_demo')
        self.assertEqual(hr_user.role, User.Role.HR)
        self.assertEqual(hr_user.organization.tax_id, '0000000000')
        self.assertTrue(hr_user.check_password('HrDemo123!'))

    def test_seed_keeps_organization_custom_factors(self):
        custom_factor = ExposureFactor.objects.create(
            category=ExposureFactor.Category.OTHER,
            name='Własny czynnik organizacji',
            organization=self.organization,
            created_by=self.user,
        )

        self.seed_catalog()

        self.assertTrue(ExposureFactor.objects.filter(pk=custom_factor.pk).exists())

    def test_disclaimer_is_visible(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertContains(response, 'Domyślna lista ma charakter demonstracyjny')

    def test_referral_form_contains_five_categories(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_create'))

        for _, label in ExposureFactor.Category.choices:
            self.assertContains(response, label)

    def test_referral_form_factor_count_matches_seed(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        response = self.client.get(reverse('referral_create'))
        content = response.content.decode('utf-8')

        self.assertEqual(content.count('name="exposure_factors"'), 100)

    def test_pages_use_base_template_shell(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        for url_name in ['home', 'employee_list', 'exposure_factor_list', 'referral_create']:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, 'class="app-header"')
                self.assertContains(response, 'Telemedi Occupational Health MVP')

    def test_django_messages_are_displayed(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('exposure_factor_create'), {
            'category': ExposureFactor.Category.OTHER,
            'name': 'Komunikat testowy',
        }, follow=True)

        self.assertContains(response, 'Dodano własny czynnik narażenia.')

    def test_polish_catalog_names_render_correctly(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        response = self.client.get(reverse('exposure_factor_list'))

        self.assertContains(response, 'Hałas infradźwiękowy')
        self.assertContains(response, 'Środki dezynfekcyjne')
        self.assertContains(response, 'Praca na wysokości')

    def test_catalog_html_has_no_known_mojibake(self):
        self.seed_catalog()
        self.client.force_login(self.user)

        responses = [
            self.client.get(reverse('exposure_factor_list')),
            self.client.get(reverse('referral_create')),
        ]

        for response in responses:
            text = response.content.decode('utf-8')
            for sequence in MOJIBAKE_SEQUENCES:
                self.assertNotIn(sequence, text)
