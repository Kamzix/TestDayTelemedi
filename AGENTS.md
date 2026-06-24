# Zasady pracy

## Stack

- Python 3.13
- Django 5.2 LTS
- SQLite
- Django Templates
- Lokalny CSS
- openpyxl
- ReportLab

## Ograniczenia technologiczne

- Bez Reacta.
- Bez npm.
- Bez osobnego REST API.
- Bez Dockera.
- Bez Redis.
- Bez Celery.
- Bez mikroserwisow.
- Bez zewnetrznych uslug.

## Priorytety i styl pracy

- Priorytetem jest dzialajacy przeplyw end-to-end.
- Stosuj KISS, DRY i SOLID pragmatycznie.
- Nie wykonuj niezwiazanych refaktorow.
- Nie zmieniaj ani nie usuwaj istniejacych plikow bez uzasadnienia.
- Nie dotykaj sekretow ani plikow `.env`.
- PDF i import XLSX maja byc wydzielone do prostych helperow lub serwisow.
- Po kazdym etapie uruchamiaj tylko testy zwiazane ze zmiana.
- Pelny zestaw testow uruchom dopiero przed oddaniem.
- Oszczedzaj tokeny: nie analizuj wielokrotnie calego repozytorium.
- Przed zmianami sprawdzaj `git status`.
- Po kazdym etapie raportuj:
  - zmienione pliki,
  - wykonane komendy,
  - wyniki testow,
  - co dziala,
  - problemy i ryzyka,
  - jeden nastepny krok.

## Bezpieczenstwo tenantow

- Dane tenantowe musza byc zawsze filtrowane po organizacji zalogowanego uzytkownika.
- Nie wolno ufac `organization_id` z formularza lub URL.
- Nie wolno pobierac obiektow tenantowych globalnym `Model.objects.get(id=...)`.
- Obiekt innej organizacji ma zwracac 404 albo bezpieczna odmowe dostepu.
- Manager moze tworzyc konta HR tylko we wlasnej organizacji.
- Nie ma publicznej rejestracji.

## Domena

- Aplikacja generuje skierowanie na badania, a nie orzeczenie lekarskie.

## Wymagania Telemedi

- Projekt ma pokazywac ownership i dowiezienie dzialajacego przeplywu end-to-end.
- Decyzje technologiczne musza byc uzasadnione i zrozumiale.
- Kod ma byc gotowy do code review: czytelny, testowalny i bez przypadkowych zmian.
- Wymagane sa logiczne commity Git opisujace spojne etapy pracy.
- README ma zawierac sposob uruchomienia, architekture, testy i kompromisy.
- AI jest narzedziem wykonawczym, ale autor projektu odpowiada za decyzje, testy i wynik.
- Wzorce zastosowane w projekcie powinny byc mozliwe do przeniesienia do PHP i Reacta.
