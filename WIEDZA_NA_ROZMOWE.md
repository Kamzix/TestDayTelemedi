# Wiedza na rozmowe techniczna

## Decyzje technologiczne

- Wybrano Django zamiast PHP/Laravela, bo w 4-godzinnym timeboxie Django daje gotowe auth, sesje, CSRF, ORM, migracje, admin i test client. To skraca droge do dzialajacego end-to-end MVP.
- Laravel tez bylby dobrym frameworkiem webowym, ale projekt juz zostal ustawiony na Python 3.13 i Django 5.2 LTS, a Django pasuje do prostego monolitu bez REST API, Reacta i uslug zewnetrznych.
- Projekt jest celowo prosty: Django Templates, SQLite i lokalne formularze wystarczaja na etap rekrutacyjny.

## Custom user model

- Custom user model to wlasny model uzytkownika, ktory dziedziczy po `AbstractUser`.
- Zostawiamy standardowe pola Django, ale dodajemy pola domenowe: `organization` i `role`.
- Utworzono go na poczatku, bo zmiana `AUTH_USER_MODEL` po wykonaniu migracji i dodaniu danych bywa kosztowna i ryzykowna.
- Dzieki temu kazdy uzytkownik aplikacji od razu ma przypisana organizacje i role.

## Migracje Django

- Migracja Django to plik opisujacy zmiane struktury bazy danych, np. utworzenie tabeli albo dodanie kolumny.
- `makemigrations` tworzy pliki migracji na podstawie modeli.
- `migrate` wykonuje te migracje na bazie SQLite.
- Migracje pozwalaja odtworzyc schemat bazy w przewidywalny sposob.

## Organization jako tenant

- `Organization` reprezentuje firme/organizacje klienta.
- Dane tenantowe, np. pracownicy, sa przypisane do jednej organizacji przez `ForeignKey`.
- Zalogowany uzytkownik ma jedna organizacje w polu `organization`.
- Kazde zapytanie do danych biznesowych musi byc ograniczone do `request.user.organization`.

## Role MANAGER i HR

- `MANAGER` ma szersze uprawnienia administracyjne w swojej organizacji.
- Manager moze tworzyc konta HR, ale tylko w swojej organizacji.
- `HR` moze korzystac z funkcji operacyjnych, ale nie moze otworzyc formularza tworzenia uzytkownikow.
- Nie ma publicznej rejestracji, wiec konta powstaja kontrolowanie.

## Wymuszanie organizacji po stronie backendu

- Formularze nie pokazuja pola `organization`.
- Backend ignoruje `organization` przeslane w POST.
- Przy tworzeniu HR ustawiane jest `user.organization = request.user.organization`.
- Przy tworzeniu pracownika ustawiane jest `employee.organization = request.user.organization`.
- Import XLSX dostaje organizacje z zalogowanego uzytkownika, a nie z arkusza.

## Zmiana ID w URL

- Samo ID w URL nie moze dawac dostepu do danych innej firmy.
- Edycja pracownika uzywa pobrania scope'owanego po organizacji: `pk=pk` oraz `organization=request.user.organization`.
- Jesli obiekt istnieje, ale nalezy do innej organizacji, aplikacja zwraca 404.
- To chroni przed prostym atakiem IDOR, czyli zmiana identyfikatora w URL.

## ModelForm, widok i template

- `ModelForm` buduje formularz na podstawie modelu i wykonuje walidacje pol.
- Widok obsluguje request: dla GET pokazuje formularz lub liste, dla POST waliduje dane i zapisuje obiekt.
- Template renderuje HTML dla uzytkownika.
- W tym projekcie formularz pracownika nie zawiera pola `organization`, wiec uzytkownik nie moze wybrac firmy recznie.

## Import XLSX przez openpyxl

- `openpyxl` czyta plik XLSX bez potrzeby instalowania Excela.
- Pierwszy wiersz arkusza jest traktowany jako naglowki.
- Import sprawdza wymagane kolumny, pomija puste wiersze i zapisuje poprawne rekordy.
- Bledny wiersz nie przerywa calego importu: blad jest dopisywany do raportu z numerem wiersza.
- Kazdy poprawny wiersz tworzy nowego pracownika, bez aktualizowania istniejacych.

## Walidacja pracownika

- Pracownik musi miec wymagane dane podstawowe: imie, nazwisko, miasto, ulice, numer budynku i stanowisko.
- Pracownik musi miec PESEL albo komplet: data urodzenia oraz dokument tozsamosci.
- PESEL nie ma jeszcze walidacji sumy kontrolnej; sprawdzane jest tylko, czy ma dokladnie 11 cyfr.
- Ta sama walidacja modelu jest uzywana przez reczny formularz i import XLSX.

## Testy

- Testy logowania potwierdzaja, ze niezalogowany uzytkownik jest przekierowany do `/login/`.
- Testy rol potwierdzaja, ze manager otwiera formularz tworzenia HR, a HR dostaje 403.
- Testy tworzenia HR potwierdzaja, ze backend wymusza role HR i organizacje managera.
- Testy pracownikow potwierdzaja, ze lista pokazuje tylko pracownikow wlasnej organizacji.
- Test edycji potwierdza, ze pracownik innej organizacji zwraca 404.
- Testy formularza potwierdzaja ignorowanie przeslanego `organization`.
- Testy importu XLSX potwierdzaja zapis poprawnego wiersza, raportowanie blednego wiersza i brak przerwania importu.

## Django ORM

- Django ORM pozwala pracowac na modelach Pythona zamiast pisac recznie SQL dla typowych operacji.
- Model opisuje tabele, pola opisuja kolumny, a queryset opisuje zapytanie do bazy.
- ORM ulatwia filtrowanie tenantowe, np. `Employee.objects.filter(organization=request.user.organization)`.

## TextChoices

- `TextChoices` to wygodny sposob definiowania ograniczonej listy wartosci tekstowych dla pola modelu.
- W `ExposureFactor` kategorie sa jawne: `PHYSICAL`, `DUST`, `CHEMICAL`, `BIOLOGICAL`, `OTHER`.
- Kod zapisuje stabilna wartosc techniczna, a template moze pokazac czytelna etykiete.

## Globalne czynniki i tenant isolation

- Domyslne czynniki maja `organization=None`, bo sa wspoldzielone przez wszystkie organizacje.
- Wlasny czynnik ma `organization` ustawiona na organizacje zalogowanego uzytkownika.
- Globalny rekord jest jeden w bazie, ale moze byc wyswietlany kazdemu tenantowi.
- Lista czynnikow laczy dane globalne i dane organizacji przez warunek: `is_default=True` albo `organization=request.user.organization`.
- Czynnik innej organizacji nie pasuje do tego querysetu, wiec nie jest widoczny.

## Usuwanie, POST i CSRF

- Usuwanie odbywa sie tylko przez POST, bo GET powinien byc bezpieczny i nie zmieniac danych.
- Formularz usuwania ma token CSRF, ktory chroni przed wykonaniem akcji z obcej strony.
- Widok delete pobiera tylko czynnik `is_default=False` oraz z organizacji uzytkownika.
- Domyslny czynnik i czynnik innej organizacji zwracaja 404, zeby nie ujawniac, czy taki obiekt istnieje.

## Testy czynnikow narazenia

- Testy potwierdzaja, ze uzytkownik widzi czynniki domyslne i wlasne.
- Testy potwierdzaja, ze czynnik innej organizacji nie pojawia sie na liscie.
- Test create potwierdza ignorowanie przeslanych `organization`, `is_default` i `created_by`.
- Testy delete potwierdzaja blokade usuwania domyslnych i cudzych czynnikow.
- Test GET delete potwierdza, ze wejscie przez GET nie wykonuje operacji.

## Relacje i skierowania

- `ForeignKey` to relacja z jednego modelu do drugiego, zapisana w bazie jako klucz obcy.
- Relacja jeden-do-wielu oznacza, ze jeden rekord nadrzedny moze miec wiele rekordow podrzednych, np. jedno skierowanie ma wiele `ReferralExposure`.
- `ReferralExposure` jest osobnym modelem posrednim, bo kazdy czynnik w skierowaniu ma dodatkowe dane: opis narazenia i opcjonalny wynik pomiaru.
- Czynnikow nie zapisujemy jako tekstu CSV, bo wtedy tracimy relacje, walidacje, integralnosc danych i mozliwosc latwego filtrowania.
- Constraint unikalnosci pilnuje, zeby ten sam czynnik nie byl przypisany dwa razy do jednego skierowania albo jednego szablonu.
- Transakcja atomowa oznacza, ze zapis skierowania, czynnikow i ewentualnego szablonu udaje sie w calosci albo w calosci sie cofa.

## Tenant scope w skierowaniach

- `employee`, `exposure_factor` i `template` musza byc tenant-scoped, bo kazdy z tych obiektow moze ujawnic dane innej firmy.
- Pracownik w formularzu pochodzi tylko z organizacji zalogowanego uzytkownika.
- Czynniki w formularzu to czynniki domyslne albo czynniki organizacji uzytkownika.
- Szablon ladowany przez `?template=<id>` jest pobierany po `pk` oraz `organization=request.user.organization`.
- Dane `organization`, `created_by` i `status` z POST sa ignorowane; backend ustawia je sam.

## Q i dynamiczne pola POST

- `Q` pozwala budowac warunki OR w querysetach, np. `is_default=True` albo `organization=user.organization`.
- `?template=<id>` to query parameter w URL, ktory przekazuje opcjonalny identyfikator szablonu do widoku.
- Wybrano zwykly request/response zamiast AJAX, bo MVP ma byc proste, czytelne i latwe do przetestowania w timeboxie.
- Dynamiczne pola czynnikow sa walidowane po stronie backendu: ID czynnika musi nalezec do dozwolonego querysetu, a opis narazenia jest wymagany.
- Testy skierowan sprawdzaja IDOR: cudzy pracownik, cudzy czynnik, cudzy szablon i cudze skierowanie sa odrzucane albo zwracaja 404.

## is_overdue

- `is_overdue` to property modelu `Referral`.
- Zwraca `True`, gdy termin jest w przeszlosci, a status nie jest `COMPLETED` ani `CANCELLED`.
- Dzieki temu lista skierowan moze pokazac badge `PRZETERMINOWANE` bez duplikowania logiki w template.

## Mapowanie do stacku Telemedi

- Django ORM odpowiada roli Eloquent w Laravelu albo Doctrine w Symfony.
- Django View odpowiada kontrolerowi PHP.
- Django Template odpowiada Blade albo Twig.
- Django Form odpowiada walidacji requestu/formularza.
- Modele posrednie odpowiadaja normalnym tabelom relacyjnym w dowolnym ORM.

## PDF skierowania

- HTTP response z `application/pdf` oznacza, ze endpoint zwraca dokument PDF, a przegladarka moze go pobrac albo wyswietlic.
- Generator PDF jest osobnym serwisem, bo widok powinien odpowiadac za pobranie danych i odpowiedz HTTP, a nie za sklad dokumentu.
- Separation of concerns oznacza oddzielenie odpowiedzialnosci: widok, logika PDF, modele i testy maja osobne role.
- Uzyto ReportLab, bo jest dostepny w stacku i pozwala generowac PDF lokalnie bez uslug zewnetrznych.
- Uzyto Platypus, bo lepiej obsluguje akapity, tabele i przechodzenie tekstu na kolejne strony niz reczne pozycjonowanie.
- Polskie znaki sa obslugiwane przez wykrycie lokalnej czcionki TrueType, np. Arial z Windows, i zarejestrowanie jej w ReportLab.
- Plikow czcionek systemowych nie dodajemy do repo, bo sa zalezne od systemu i moga miec ograniczenia licencyjne.
- Pobieranie PDF jest zabezpieczone przed IDOR przez pobranie skierowania po `pk` oraz `organization=request.user.organization`.
- `select_related` pobiera relacje ForeignKey jednym zapytaniem SQL, np. organizacje i pracownika.
- `prefetch_related` pobiera relacje wiele rekordow, np. czynniki skierowania, w dodatkowym kontrolowanym zapytaniu.
- Testujemy naglowek `%PDF`, bo potwierdza format pliku bez kruchego porownywania calej binarnej zawartosci.
- Skierowanie jest dokumentem wystawianym przez pracodawce na badania. Orzeczenie lekarskie wystawia lekarz i nie jest generowane w tej aplikacji.

## Mapowanie PDF do PHP

- Serwis PDF Django/Python odpowiada osobnej klasie serwisowej w PHP.
- ReportLab odpowiada bibliotece PDF w PHP, np. Dompdf albo TCPDF.
- `HttpResponse` odpowiada `Response` w Symfony albo Laravelu.
- Tenant-scoped query odpowiada scope albo query builderowi w PHP z warunkiem organizacji.

## Mozliwe pytania na rozmowie technicznej

**Dlaczego Django, a nie Laravel?**  
Django mialo wiecej gotowych elementow potrzebnych w timeboxie: auth, ORM, migracje, formularze, szablony, CSRF i test client. Celem bylo szybkie, bezpieczne MVP end-to-end.

**Dlaczego custom user model powstal od razu?**  
Bo uzytkownik od poczatku potrzebuje organizacji i roli. Zmiana modelu uzytkownika po czasie jest trudniejsza, szczegolnie po migracjach i danych.

**Jak chronisz dane jednej firmy przed druga?**  
Kazde zapytanie po dane tenantowe jest filtrowane po `request.user.organization`. Przy edycji uzywam jednoczesnie `pk` i `organization`, wiec cudzy rekord daje 404.

**Czy mozna przeslac `organization` w POST i zapisac pracownika do innej firmy?**  
Nie. Formularz nie ma tego pola, a backend i tak ustawia organizacje z zalogowanego uzytkownika.

**Jak zablokowano tworzenie managerow przez formularz HR?**  
Formularz przyjmuje tylko dane konta. Rola nie jest polem formularza, a backend zawsze ustawia `role = HR`.

**Co sie dzieje, gdy jeden wiersz XLSX jest bledny?**  
Ten wiersz jest pomijany i trafia do listy bledow z numerem wiersza. Poprawne wiersze z tego samego pliku nadal sa zapisywane.

**Dlaczego walidacja pracownika jest w modelu?**  
Bo wtedy moze byc uzyta zarowno przez `ModelForm`, jak i import XLSX przez `full_clean()`. Nie trzeba duplikowac reguly.

**Co potwierdzaja testy?**  
Potwierdzaja logowanie, role, izolacje organizacji, ignorowanie danych tenantowych z POST, walidacje pracownika oraz odporny import XLSX.

**Czym jest Django ORM?**  
To warstwa, ktora mapuje klasy modeli na tabele w bazie i pozwala pisac zapytania w Pythonie zamiast recznie w SQL.

**Po co uzyc `TextChoices` dla kategorii czynnikow?**  
Dzieki temu kategorie maja stale wartosci techniczne i czytelne etykiety, a formularz automatycznie pokazuje poprawne opcje.

**Dlaczego domyslne czynniki maja `organization=None`?**  
Bo sa globalne i wspoldzielone przez wszystkie organizacje. Nie naleza do jednego konkretnego tenanta.

**Jak lista pokazuje globalne i wlasne czynniki naraz?**  
Queryset wybiera rekordy, gdzie `is_default=True`, albo rekordy z `organization` rowna organizacji zalogowanego uzytkownika.

**Dlaczego delete jest tylko POST-em?**  
Bo GET nie powinien zmieniac danych. POST plus CSRF zmniejsza ryzyko przypadkowego lub zewnetrznego usuniecia.

**Dlaczego dla cudzego czynnika zwracamy 404?**  
Zeby nie potwierdzac, ze taki rekord istnieje. Dla uzytkownika spoza organizacji obiekt jest niedostepny.

**Dlaczego `ReferralExposure` jest osobnym modelem?**  
Bo samo polaczenie skierowania z czynnikiem nie wystarcza. Dla kazdego czynnika trzeba zapisac opis narazenia i opcjonalny wynik pomiaru.

**Dlaczego nie zapisac czynnikow jako tekstu po przecinku?**  
Bo tekst CSV jest trudny do walidacji, filtrowania i utrzymania. Relacyjny model daje integralnosc danych i constrainty.

**Po co transakcja atomowa przy tworzeniu skierowania?**  
Zeby nie zostawic polowicznego zapisu. Skierowanie, jego czynniki i ewentualny szablon zapisuja sie razem albo wcale.

**Jak bronisz sie przed cudzym pracownikiem w POST?**  
Pole `employee` ma queryset ograniczony do organizacji uzytkownika. ID pracownika z innej organizacji nie przechodzi walidacji formularza.

**Jak bronisz sie przed cudzym czynnikiem w dynamicznych polach POST?**  
Widok sprawdza ID czynnika w dozwolonym querysecie: domyslne czynniki albo czynniki organizacji uzytkownika.

**Jak dziala uzycie szablonu przez `?template=<id>`?**  
Widok pobiera szablon po ID i organizacji uzytkownika. Jesli szablon jest cudzy, zwraca 404.

**Dlaczego bez AJAX?**  
Bo wymaganie MVP da sie zrobic prosciej przez zwykly request/response. To mniej kodu, mniej ryzyka i latwiejsze testy.

**Dlaczego generator PDF jest serwisem, a nie kodem w widoku?**  
Widok ma pobrac skierowanie i zwrocic odpowiedz HTTP. Serwis odpowiada tylko za zbudowanie PDF, wiec kod jest prostszy do testowania i review.

**Jak obslugiwane sa polskie znaki w PDF?**  
Generator wyszukuje lokalna czcionke TrueType obslugujaca polskie znaki, rejestruje ja w ReportLab i ustawia w stylach dokumentu.

**Dlaczego nie dodajesz czcionki do repo?**  
Bo to plik systemowy, zalezy od srodowiska i moze miec licencje, ktora nie pozwala na kopiowanie do projektu.

**Jak zabezpieczono pobieranie PDF przed IDOR?**  
Skierowanie jest pobierane po ID oraz organizacji zalogowanego uzytkownika. Cudze skierowanie zwraca 404.

**Dlaczego testujesz `%PDF`, a nie caly plik?**  
PDF zawiera metadane i binarna strukture, ktore moga sie roznic miedzy uruchomieniami. Sygnatura i Content-Type potwierdzaja najwazniejszy kontrakt.

**Czym rozni sie skierowanie od orzeczenia?**  
Skierowanie wystawia pracodawca, aby pracownik wykonal badania. Orzeczenie wystawia lekarz po badaniu i aplikacja go nie generuje.
