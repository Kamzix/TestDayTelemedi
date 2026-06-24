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
            (ExposureFactor.Category.PHYSICAL, 'Hałas'),
            (ExposureFactor.Category.PHYSICAL, 'Hałas infradźwiękowy'),
            (ExposureFactor.Category.PHYSICAL, 'Hałas ultradźwiękowy'),
            (ExposureFactor.Category.PHYSICAL, 'Drgania mechaniczne przenoszone na kończyny górne'),
            (ExposureFactor.Category.PHYSICAL, 'Drgania mechaniczne o działaniu ogólnym'),
            (ExposureFactor.Category.PHYSICAL, 'Promieniowanie jonizujące'),
            (ExposureFactor.Category.PHYSICAL, 'Promieniowanie ultrafioletowe'),
            (ExposureFactor.Category.PHYSICAL, 'Promieniowanie podczerwone'),
            (ExposureFactor.Category.PHYSICAL, 'Promieniowanie laserowe'),
            (ExposureFactor.Category.PHYSICAL, 'Pole elektromagnetyczne'),
            (ExposureFactor.Category.PHYSICAL, 'Mikroklimat gorący'),
            (ExposureFactor.Category.PHYSICAL, 'Mikroklimat zimny'),
            (ExposureFactor.Category.PHYSICAL, 'Praca w warunkach podwyższonego ciśnienia'),
            (ExposureFactor.Category.PHYSICAL, 'Praca w warunkach obniżonego ciśnienia'),
            (ExposureFactor.Category.PHYSICAL, 'Niedostateczne oświetlenie'),
            (ExposureFactor.Category.PHYSICAL, 'Oświetlenie powodujące olśnienie'),
            (ExposureFactor.Category.PHYSICAL, 'Zmienna temperatura otoczenia'),
            (ExposureFactor.Category.PHYSICAL, 'Wysoka wilgotność powietrza'),
            (ExposureFactor.Category.PHYSICAL, 'Niska wilgotność powietrza'),
            (ExposureFactor.Category.PHYSICAL, 'Kontakt z gorącymi lub zimnymi powierzchniami'),
            (ExposureFactor.Category.DUST, 'Pył całkowity'),
            (ExposureFactor.Category.DUST, 'Pył respirabilny'),
            (ExposureFactor.Category.DUST, 'Pył drewna twardego'),
            (ExposureFactor.Category.DUST, 'Pył drewna miękkiego'),
            (ExposureFactor.Category.DUST, 'Pył zawierający krzemionkę krystaliczną'),
            (ExposureFactor.Category.DUST, 'Pył azbestu'),
            (ExposureFactor.Category.DUST, 'Pył węglowy'),
            (ExposureFactor.Category.DUST, 'Pyły metali'),
            (ExposureFactor.Category.DUST, 'Dymy spawalnicze'),
            (ExposureFactor.Category.DUST, 'Pył mączny'),
            (ExposureFactor.Category.DUST, 'Pył zbożowy'),
            (ExposureFactor.Category.DUST, 'Pył bawełniany'),
            (ExposureFactor.Category.DUST, 'Pył cementowy'),
            (ExposureFactor.Category.DUST, 'Pył gipsowy'),
            (ExposureFactor.Category.DUST, 'Pył ceramiczny'),
            (ExposureFactor.Category.DUST, 'Pył z wełny mineralnej'),
            (ExposureFactor.Category.DUST, 'Pył papierniczy i celulozowy'),
            (ExposureFactor.Category.DUST, 'Pył tworzyw sztucznych'),
            (ExposureFactor.Category.DUST, 'Sadza i pyły ze spalania'),
            (ExposureFactor.Category.DUST, 'Pyły organiczne pochodzenia roślinnego'),
            (ExposureFactor.Category.CHEMICAL, 'Rozpuszczalniki organiczne'),
            (ExposureFactor.Category.CHEMICAL, 'Środki dezynfekcyjne'),
            (ExposureFactor.Category.CHEMICAL, 'Środki czyszczące i detergenty'),
            (ExposureFactor.Category.CHEMICAL, 'Kwasy'),
            (ExposureFactor.Category.CHEMICAL, 'Zasady i substancje żrące'),
            (ExposureFactor.Category.CHEMICAL, 'Farby i lakiery'),
            (ExposureFactor.Category.CHEMICAL, 'Kleje'),
            (ExposureFactor.Category.CHEMICAL, 'Żywice epoksydowe'),
            (ExposureFactor.Category.CHEMICAL, 'Izocyjaniany'),
            (ExposureFactor.Category.CHEMICAL, 'Formaldehyd'),
            (ExposureFactor.Category.CHEMICAL, 'Amoniak'),
            (ExposureFactor.Category.CHEMICAL, 'Chlor i jego związki'),
            (ExposureFactor.Category.CHEMICAL, 'Ozon'),
            (ExposureFactor.Category.CHEMICAL, 'Tlenek węgla'),
            (ExposureFactor.Category.CHEMICAL, 'Dwutlenek węgla'),
            (ExposureFactor.Category.CHEMICAL, 'Paliwa i ich pary'),
            (ExposureFactor.Category.CHEMICAL, 'Oleje, smary i płyny technologiczne'),
            (ExposureFactor.Category.CHEMICAL, 'Pestycydy i środki ochrony roślin'),
            (ExposureFactor.Category.CHEMICAL, 'Metale ciężkie i ich związki'),
            (ExposureFactor.Category.CHEMICAL, 'Czynniki chłodnicze'),
            (ExposureFactor.Category.BIOLOGICAL, 'Bakterie'),
            (ExposureFactor.Category.BIOLOGICAL, 'Wirusy'),
            (ExposureFactor.Category.BIOLOGICAL, 'Grzyby i pleśnie'),
            (ExposureFactor.Category.BIOLOGICAL, 'Pasożyty'),
            (ExposureFactor.Category.BIOLOGICAL, 'Materiał biologiczny pochodzenia ludzkiego'),
            (ExposureFactor.Category.BIOLOGICAL, 'Krew i inne płyny ustrojowe'),
            (ExposureFactor.Category.BIOLOGICAL, 'Materiał biologiczny pochodzenia zwierzęcego'),
            (ExposureFactor.Category.BIOLOGICAL, 'Czynniki odzwierzęce'),
            (ExposureFactor.Category.BIOLOGICAL, 'Ścieki i osady ściekowe'),
            (ExposureFactor.Category.BIOLOGICAL, 'Odpady komunalne i medyczne'),
            (ExposureFactor.Category.BIOLOGICAL, 'Zanieczyszczona gleba'),
            (ExposureFactor.Category.BIOLOGICAL, 'Bioaerozole'),
            (ExposureFactor.Category.BIOLOGICAL, 'Alergeny pochodzenia roślinnego'),
            (ExposureFactor.Category.BIOLOGICAL, 'Alergeny pochodzenia zwierzęcego'),
            (ExposureFactor.Category.BIOLOGICAL, 'Endotoksyny bakteryjne'),
            (ExposureFactor.Category.BIOLOGICAL, 'Bakterie z rodzaju Legionella'),
            (ExposureFactor.Category.BIOLOGICAL, 'Prątki gruźlicy'),
            (ExposureFactor.Category.BIOLOGICAL, 'Wirusy zapalenia wątroby HBV i HCV'),
            (ExposureFactor.Category.BIOLOGICAL, 'Koronawirusy, w tym SARS-CoV-2'),
            (ExposureFactor.Category.BIOLOGICAL, 'Kontakt z kleszczami i innymi wektorami chorób'),
            (ExposureFactor.Category.OTHER, 'Praca na wysokości'),
            (ExposureFactor.Category.OTHER, 'Praca przy monitorze ekranowym'),
            (ExposureFactor.Category.OTHER, 'Ręczne przenoszenie ciężarów'),
            (ExposureFactor.Category.OTHER, 'Wymuszona pozycja ciała'),
            (ExposureFactor.Category.OTHER, 'Powtarzalne ruchy kończyn'),
            (ExposureFactor.Category.OTHER, 'Długotrwała praca stojąca'),
            (ExposureFactor.Category.OTHER, 'Długotrwała praca siedząca'),
            (ExposureFactor.Category.OTHER, 'Praca zmianowa'),
            (ExposureFactor.Category.OTHER, 'Praca w porze nocnej'),
            (ExposureFactor.Category.OTHER, 'Obciążenie psychiczne i stres'),
            (ExposureFactor.Category.OTHER, 'Kierowanie pojazdami'),
            (ExposureFactor.Category.OTHER, 'Obsługa maszyn i urządzeń w ruchu'),
            (ExposureFactor.Category.OTHER, 'Kontakt z ostrymi narzędziami'),
            (ExposureFactor.Category.OTHER, 'Ryzyko poślizgnięcia, potknięcia lub upadku'),
            (ExposureFactor.Category.OTHER, 'Praca w przestrzeniach zamkniętych'),
            (ExposureFactor.Category.OTHER, 'Praca w odosobnieniu'),
            (ExposureFactor.Category.OTHER, 'Prace pożarowo niebezpieczne'),
            (ExposureFactor.Category.OTHER, 'Praca w atmosferze zagrożonej wybuchem'),
            (ExposureFactor.Category.OTHER, 'Zagrożenie porażeniem prądem elektrycznym'),
            (ExposureFactor.Category.OTHER, 'Praca w pobliżu ruchu drogowego lub pojazdów'),
        ]
        canonical_keys = set(default_factors)
        canonical_factors = {}
        created_factors = 0
        for category, name in default_factors:
            factor, factor_created = ExposureFactor.objects.get_or_create(
                category=category,
                name=name,
                is_default=True,
                organization=None,
                defaults={
                    'created_by': None,
                },
            )
            if factor.created_by_id:
                factor.created_by = None
                factor.save(update_fields=['created_by'])
            canonical_factors[(category, name)] = factor
            if factor_created:
                created_factors += 1
        legacy_replacements = {
            (ExposureFactor.Category.PHYSICAL, 'Halas'): (ExposureFactor.Category.PHYSICAL, 'Hałas'),
            (
                ExposureFactor.Category.PHYSICAL,
                'Drgania mechaniczne',
            ): (
                ExposureFactor.Category.PHYSICAL,
                'Drgania mechaniczne przenoszone na kończyny górne',
            ),
            (ExposureFactor.Category.DUST, 'Pyly przemyslowe'): (ExposureFactor.Category.DUST, 'Pył całkowity'),
            (ExposureFactor.Category.DUST, 'Pyly drewna'): (ExposureFactor.Category.DUST, 'Pył drewna twardego'),
            (
                ExposureFactor.Category.CHEMICAL,
                'Srodki dezynfekcyjne',
            ): (
                ExposureFactor.Category.CHEMICAL,
                'Środki dezynfekcyjne',
            ),
            (
                ExposureFactor.Category.BIOLOGICAL,
                'Kontakt z materialem biologicznym',
            ): (
                ExposureFactor.Category.BIOLOGICAL,
                'Materiał biologiczny pochodzenia ludzkiego',
            ),
            (ExposureFactor.Category.BIOLOGICAL, 'Bakterie i wirusy'): (ExposureFactor.Category.BIOLOGICAL, 'Bakterie'),
            (ExposureFactor.Category.OTHER, 'Praca na wysokosci'): (ExposureFactor.Category.OTHER, 'Praca na wysokości'),
        }
        removed_legacy_defaults = 0
        for factor in ExposureFactor.objects.filter(is_default=True, organization=None):
            if (factor.category, factor.name) not in canonical_keys:
                replacement_key = legacy_replacements.get((factor.category, factor.name))
                replacement = canonical_factors.get(replacement_key)
                if replacement:
                    factor.referral_exposures.update(exposure_factor=replacement)
                    factor.template_exposures.update(exposure_factor=replacement)
                factor.delete()
                removed_legacy_defaults += 1

        action = 'created' if created else 'updated'
        self.stdout.write(self.style.SUCCESS(f'Demo manager {action}.'))
        self.stdout.write(f'Default exposure factors present: {len(default_factors)}.')
        self.stdout.write(f'Default exposure factors newly created: {created_factors}.')
        self.stdout.write(f'Legacy default exposure factors removed: {removed_legacy_defaults}.')
        self.stdout.write('Demo login only for local demo environment:')
        self.stdout.write('username: manager')
        self.stdout.write('password: Manager123!')
        self.stdout.write('organization: Telemedi Demo Employer')
