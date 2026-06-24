from django.core.management.base import BaseCommand

from occupational_health.models import ExposureFactor, Organization, User


class Command(BaseCommand):
    help = 'Create demo organization and manager account.'

    def handle(self, *args, **options):
        organization, _ = Organization.objects.update_or_create(
            tax_id='0000000000',
            defaults={
                'name': 'Telemedi Demo Employer',
                'address': 'Rzymowskiego 53',
                'city': 'Warszawa',
                'postal_code': '02-697',
            },
        )
        manager, created = User.objects.get_or_create(
            username='manager',
            defaults={
                'organization': organization,
                'role': User.Role.MANAGER,
                'email': '',
            },
        )
        manager.organization = organization
        manager.role = User.Role.MANAGER
        manager.set_password('Manager123!')
        manager.save()

        default_factors = [
            (ExposureFactor.Category.PHYSICAL, 'Halas'),
            (ExposureFactor.Category.PHYSICAL, 'Drgania mechaniczne'),
            (ExposureFactor.Category.DUST, 'Pyly przemyslowe'),
            (ExposureFactor.Category.DUST, 'Pyly drewna'),
            (ExposureFactor.Category.CHEMICAL, 'Srodki dezynfekcyjne'),
            (ExposureFactor.Category.CHEMICAL, 'Rozpuszczalniki organiczne'),
            (ExposureFactor.Category.BIOLOGICAL, 'Kontakt z materialem biologicznym'),
            (ExposureFactor.Category.BIOLOGICAL, 'Bakterie i wirusy'),
            (ExposureFactor.Category.OTHER, 'Praca na wysokosci'),
            (ExposureFactor.Category.OTHER, 'Praca przy monitorze ekranowym'),
        ]
        created_factors = 0
        for category, name in default_factors:
            _, factor_created = ExposureFactor.objects.update_or_create(
                category=category,
                name=name,
                is_default=True,
                organization=None,
                defaults={
                    'created_by': None,
                },
            )
            if factor_created:
                created_factors += 1

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'Demo manager {action}.'))
        self.stdout.write(f'Default exposure factors present: {len(default_factors)}.')
        self.stdout.write(f'Default exposure factors newly created: {created_factors}.')
        self.stdout.write('Demo login only for local demo environment:')
        self.stdout.write('username: manager')
        self.stdout.write('password: Manager123!')
        self.stdout.write('organization: Telemedi Demo Employer')
