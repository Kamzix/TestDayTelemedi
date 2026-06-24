# Telemedi Occupational Health MVP

## Cel projektu

MVP aplikacji wspierającej pracodawcę i dział HR w wystawianiu skierowań na badania medycyny pracy. Aplikacja generuje skierowanie wystawiane przez pracodawcę, a nie orzeczenie lekarskie.

## Główny flow

`login -> pracownik -> czynniki narażenia -> skierowanie -> PDF -> lista i status`

## Technologie

- Python 3.13
- Django 5.2 LTS
- SQLite
- Django Templates
- lokalny CSS
- openpyxl
- ReportLab

## Uruchomienie na Windows PowerShell

Komendy od czystego repo:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

## Szybkie komendy Windows

```powershell
.\dev.cmd
.\test.cmd
.\check.cmd
```

Sa to lokalne odpowiedniki workflow `npm run dev/test`, bez dokladania Node.js do monolitu Django.

## Konto demo

- username: `manager`
- password: `Manager123!`

Dane logowania są przeznaczone wyłącznie do lokalnego demo.

## Testy

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test occupational_health
```

## Funkcje

- role `MANAGER` i `HR`
- izolacja organizacji
- pracownicy
- import XLSX
- czynniki narażenia
- skierowania
- szablony stanowisk
- PDF
- statusy
- walidacja i limity pól
- polskie znaki i UTF-8

## Bezpieczeństwo

- Dane tenantowe są filtrowane po organizacji zalogowanego użytkownika.
- Organizacja jest wymuszana backendowo przy tworzeniu HR, pracowników, czynników, skierowań i szablonów.
- Ochrona przed IDOR: obiekty szczegółowe są pobierane przez `pk` oraz `organization=request.user.organization`.
- Formularze POST używają CSRF.
- Operacje modyfikujące są wykonywane przez POST, nie przez GET.
- Tworzenie skierowania i powiązanych ekspozycji działa w transakcji atomowej.
- Walidacja backendowa nie ufa polom `organization`, `created_by`, `status` ani ID czynników z POST.

## Architektura

Projekt jest prostym monolitem Django:

- modele opisują organizacje, użytkowników, pracowników, czynniki, skierowania i szablony,
- formularze odpowiadają za walidację danych wejściowych,
- widoki realizują przepływy request/response,
- templates renderują HTML,
- services wydzielają import XLSX i generowanie PDF.

## Decyzja technologiczna

PHP było sugerowane, ale technologia była dowolna. Django wybrano ze względu na ograniczony timebox i gotowe elementy potrzebne do bezpiecznego flow end-to-end: auth, sesje, CSRF, ORM, migracje, formularze, templates, test client i generowanie odpowiedzi HTTP.

Priorytetem było kompletne, działające i testowalne MVP. Zastosowane wzorce można przenieść do PHP/Laravel/Symfony i Reacta: kontrolery, formularze/walidatory, ORM, seedery, layouty, flash messages oraz tenant-scoped queries.

## Kompromisy MVP

- SQLite zamiast produkcyjnej bazy.
- Brak automatycznej integracji z Telemedi.
- PDF jest pobierany i przekazywany ręcznie.
- Brak zaawansowanego JavaScriptu.
- Słownik czynników ma charakter demonstracyjny i pomocniczy.

## Następne kroki produkcyjne

- PostgreSQL.
- Konfiguracja przez zmienne środowiskowe.
- Audit log operacji.
- Rozszerzenie workflow statusów.
- Integracja API.
- CI/CD.
