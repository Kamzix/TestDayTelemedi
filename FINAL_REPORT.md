# Final Report

## Zakres ukończony

- Bootstrap projektu Django 5.2 LTS na Pythonie 3.13.
- Custom user z rolami `MANAGER` i `HR`.
- Model organizacji oraz izolacja tenantów.
- Logowanie i wylogowanie przez Django auth.
- Tworzenie kont HR przez managera w ramach własnej organizacji.
- CRUD pracowników oraz import XLSX.
- Słownik 100 domyślnych czynników narażenia, po 20 w każdej kategorii.
- Własne czynniki organizacji.
- Skierowania z wieloma czynnikami narażenia.
- Szablony stanowisk.
- Statusy skierowań.
- PDF skierowania na badania lekarskie.
- Walidacja, limity pól, testy negatywne i polskie znaki.
- Lekki UI oparty o Django Templates, `base.html`, lokalny CSS i Django messages.

## Wynik testów

- `manage.py check`: OK.
- `manage.py makemigrations --check --dry-run`: No changes detected.
- `manage.py test occupational_health`: 76 testów, OK.
- Audit UTF-8 i mojibake: OK.
- Audit plików lokalnych: `.venv/`, `db.sqlite3`, `.env*`, `debug.log`, `.agents/`, PDF i XLSX nie są śledzone w repo.

## Wynik smoke testu

Smoke test przeszedł automatycznie przez:

1. login managera,
2. utworzenie HR,
3. login HR,
4. utworzenie aktywnego pracownika,
5. import XLSX z jednym poprawnym i jednym błędnym wierszem,
6. dodanie własnego czynnika,
7. utworzenie skierowania z dwoma czynnikami,
8. zapis szablonu,
9. użycie szablonu,
10. zmianę statusu,
11. pobranie PDF,
12. próbę dostępu do danych innej organizacji,
13. weryfikację polskich znaków w HTML, XLSX, bazie i PDF.

Kluczowy wynik smoke testu:

- manager login: `True`
- HR login: `True`
- create employee: `302`
- import XLSX: `200`, poprawny wiersz zapisany, błędny odrzucony
- create referral: `302`, zapisano 2 ekspozycje
- template saved: 2 ekspozycje
- status: `ORDERED`
- PDF: `200`, `application/pdf`, `%PDF`, 43670 bajtów
- cudze szczegóły/PDF: `404`
- polskie znaki w HTML i bazie: `True`

## Bezpieczeństwo

- Dane tenantowe są zawsze filtrowane po organizacji zalogowanego użytkownika.
- Obiekty szczegółowe są pobierane przez `pk` i `organization=request.user.organization`.
- Backend wymusza organizację, autora i status zamiast ufać POST.
- Formularze POST używają CSRF.
- Operacje modyfikujące nie są wykonywane przez GET.
- Tworzenie skierowania i powiązanych ekspozycji działa atomowo.
- Dynamiczne ID czynników są sprawdzane przeciwko dozwolonemu querysetowi.
- Próba dostępu do danych innej organizacji zwraca 404.

## Znane kompromisy

- SQLite zamiast PostgreSQL.
- Konfiguracja produkcyjna nie została wydzielona do `.env`.
- Brak integracji API z Telemedi.
- PDF jest generowany i pobierany ręcznie.
- Brak zaawansowanego JavaScriptu.
- Domyślny słownik czynników ma charakter demonstracyjny i pomocniczy.

## Instrukcja demo krok po kroku

1. Uruchom aplikację:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

2. Otwórz aplikację w przeglądarce:

```text
http://127.0.0.1:8000/
```

3. Zaloguj się:

```text
username: manager
password: Manager123!
```

4. Pokaż dashboard, użytkownika, rolę i organizację.
5. Przejdź do pracowników i dodaj pracownika.
6. Pokaż import XLSX jako alternatywny sposób dodawania danych.
7. Przejdź do czynników narażenia i pokaż 5 kategorii oraz disclaimer.
8. Dodaj własny czynnik organizacji.
9. Utwórz skierowanie dla pracownika, wybierając minimum dwa czynniki.
10. Zapisz dane stanowiska jako szablon.
11. Pokaż listę skierowań i szczegóły.
12. Zmień status skierowania.
13. Pobierz PDF.
14. Wspomnij, że cudze dane są blokowane przez tenant-scoped queries i zwracają 404.

## Gotowość projektu do prezentacji

Projekt jest gotowy do prezentacji jako MVP dnia próbnego:

- flow end-to-end działa,
- testy przechodzą,
- dokumentacja uruchomienia jest w README,
- finalny raport opisuje zakres i kompromisy,
- kod jest wypchnięty do Git,
- lokalne notatki rozmowowe pozostają poza repo.
