# 🧠 10x-AT — moduł analizy technicznej dla AIvestor

![](./docs/banner.png)

**10x-AT** to niezależny, modularny komponent systemu **[AIvestor.pl](https://aivestor.pl)**, który realizuje wybrane aspekty **analizy technicznej rynków finansowych**.   Projekt został zaprojektowany tak, by można go było wdrożyć jako integralny fragment ekosystemu AIvestor. Aktualne repozytorium implementuje logike obliczania oraz wizualna prezentacje wyników na potrzeby **projektu zaliczoniowego ze szkolenia 10xDev**.

## 🌐 Deployment

Aktualna wersja modułu jest dostępna publicznie pod adresem:  
👉 **[https://10x.aivestor-ui.pl/](https://10x.aivestor-ui.pl/)**


## 🧩 Kontekst projektu

Referencyjny projekt **[AIvestor.pl](https://aivestor.pl)** to eksperymentalna, wieloagentowa architektura *decision intelligence* (R&D), event‑driven i human‑in‑the‑loop: łączy analizę techniczną, newsy ESPI, sentyment, profil spółek oraz strategię/inencję użytkownika wyrażoną w języku naturalnym. Nie jest produktem komercyjnym ani poradą inwestycyjną – służy do testowania hipotez (explainability, odporność architektury, spójność decyzji).

Niniejsze repozytorium (**10x-AT**) jest wyłącznie modułem analizy technicznej tego systemu; docelowo zostanie włączony do projektu referencyjnego AIvestor jako jedna z wyspecjalizowanych usług / agentów dostarczająca widoki AT, scoring ukrytej akumulacji i sygnały formacji.

Moduł koncentruje się na **analizie technicznej (Technical Analysis)**, w szczególności:
- przetwarzaniu i agregacji danych giełdowych (candlestick, volume, OBV, VIX),
- wykrywaniu formacji oraz anomalii wolumenowych,
- generowaniu sygnałów „spring" i „box pattern",
- detekcji ukrytej akumulacji (hidden accumulation),
- wizualizacji wyników w sposób interaktywny.

## ⚙️ Stack technologiczny

| Obszar | Technologia |
|--------|--------------|
| **Backend** | Python 3.12+, PostgreSQL (analiza danych, widoki analityczne) |
| **Frontend** | Streamlit (interaktywne wizualizacje), Plotly (wykresy) |
| **Baza danych** | PostgreSQL 14+ z zaawansowanymi widokami SQL |
| **Migracje** | Yoyo Migrations |
| **Testing** | Pytest |
| **Integracja** | API z platformą [AIvestor.pl](https://aivestor.pl) |
| **Deployment** | Docker / Nginx / CI-CD |

## 🚀 Cele projektu

- 🧩 stworzenie elastycznego modułu AT możliwego do integracji z różnymi źródłami danych,  
- 📊 wizualizacja i testowanie autorskich wskaźników w czasie rzeczywistym,  
- 🧠 umożliwienie połączenia analiz technicznych z warstwą AI / Machine Learning AIvestora,  
- 🌍 wdrożenie produkcyjne jako część **AIvestor Cloud Infrastructure**.

## Quick Links

- [Platform szkoleniowa 10xDevs.pl](https://10xdevs.pl)

## AI Tooling

- [GitHub Copilot](https://github.com/features/copilot)
- [ClickUp](https://app.clickup.com)
- [ChatGPT](https://chatgpt.com)
- [mermaid.live](https://www.mermaidchart.com)
- [eraser.io](https://eraser.io)

## Prerequisites

- Python 3.12 lub wyższy
- PostgreSQL 14+ (lokalnie lub zdalnie)
- pip do zarządzania zależnościami

## Installation

1. **Instalacja zależności Python:**
```bash
pip install -r requirements.txt
```

2. **Konfiguracja bazy danych:**
   - Utwórz plik `.env` na podstawie konfiguracji środowiskowej
   - Zaktualizuj dane dostępowe do PostgreSQL

3. **Utworzenie bazy danych PostgreSQL:**
```bash
createdb aivestor_at
```

4. **Uruchomienie migracji:**
```bash
yoyo apply --config yoyo.ini
```

## Running the Application

Uruchomienie aplikacji Streamlit:
```bash
streamlit run python/ui/main.py
```

Aplikacja będzie dostępna pod adresem http://localhost:8501

## Running Tests

Uruchomienie wszystkich testów:
```bash
pytest
```

Testy z pokryciem kodu:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
├── python/                   # Kod źródłowy Python
│   ├── config/              # Konfiguracja globalna
│   │   └── globals.py       # Stałe konfiguracyjne
│   ├── database/            # Warstwa dostępu do danych
│   │   ├── crud.py          # Operacje CRUD
│   │   ├── reporting.py     # Raporty i agregacje
│   │   └── users.py         # Zarządzanie użytkownikami
│   ├── etl/                 # Procesy ETL
│   │   └── calc_accum.py    # Kalkulacja wskaźników akumulacji
│   ├── tools/               # Narzędzia pomocnicze
│   │   ├── logger.py        # System logowania
│   │   ├── utils.py         # Funkcje pomocnicze
│   │   └── encryption.py    # Szyfrowanie danych
│   └── ui/                  # Interfejs użytkownika Streamlit
│       ├── main.py          # Główny punkt wejścia
│       ├── auth.py          # Autoryzacja użytkowników
│       ├── instrument_view.py  # Widok instrumentów
│       └── user_management.py  # Zarządzanie użytkownikami
├── migrations/              # Skrypty migracji Yoyo
│   ├── 0010_create_schemas.sql    # Schematy bazy danych
│   ├── 0030_create_trans_tables.sql  # Tabele transakcyjne
│   ├── 0110_create_user_config.sql   # Konfiguracja użytkowników
│   └── 0130_at.sql                   # Widoki analizy technicznej
├── tests/                   # Testy jednostkowe
│   ├── test_db.py          # Testy bazy danych
│   └── test_users.py       # Testy użytkowników
├── charts/                  # Diagramy i specyfikacje
├── docs/                    # Dokumentacja statyczna
├── logs/                    # Logi aplikacji
├── requirements.txt         # Zależności Python
├── pyproject.toml          # Metadane projektu
└── yoyo.ini                # Konfiguracja migracji
```

## Exercises

Ćwiczenia do rozwoju umiejętności AI-assisted development:

1. **Analiza techniczna** - Eksperymentowanie z nowymi wskaźnikami i algorytmami detekcji
2. **Analiza pokrycia testami** - Rozbudowa testów dla modułów analitycznych
3. **Diagramy Mermaid** - Generowanie diagramów z `/charts/request.md`
4. **Własne reguły AI** - Modyfikacja zachowań AI poprzez custom rules

## Features

- ✅ Analiza hidden accumulation (ukryta akumulacja)
- ✅ Wykrywanie formacji box pattern i spring signals
- ✅ Wieloskładnikowy scoring (C1-C5: volatility compression, volume ratio, OBV flow, no-supply, spring)
- ✅ Interaktywne wykresy Plotly z OHLCV
- ✅ System zarządzania użytkownikami z autentykacją
- ✅ Widok instrumentów z profilem spółek (kapitalizacja, branża, opis)
- ✅ Integracja z danymi BiznesRadar i XTB
- ✅ Snapshoty wskaźników z timestampami
- ✅ PostgreSQL z zaawansowanymi widokami analitycznymi
- ✅ ETL dla kalkulacji akumulacji
- ✅ System logowania i monitoringu
- ✅ Streamlit responsive UI

## Architektura analizy technicznej

### Widoki analityczne (schemat `at`)

**v_candles_1m** - Podstawowe dane OHLCV w interwale 1-minutowym

**v_base_20** - Okno 20-periodowe z podstawowymi wskaźnikami:
- ATR (Average True Range) - zmienność
- SMA/EMA - średnie kroczące
- OBV (On-Balance Volume) - przepływ wolumenu
- Up/Down volume ratio - proporcje wzrostów/spadków
- Spread statistics - analiza spreadów

**v_hidden_20** - Zaawansowana detekcja ukrytej akumulacji:
- **C1 (25%)**: Volatility compression (kontrakcja zmienności)
- **C2 (25%)**: Up/Down volume ratio (dominacja up volume)
- **C3 (30%)**: Money flow (OBV slope + flat price)
- **C4 (15%)**: No-supply signals (brak podaży)
- **C5 (5%)**: Spring detection (wybicie w dół i odwrót)
- **hidden_accum_score**: Kompozytowy wynik 0-100
- **hidden_accum_setup**: Boolean flag dla setupów >70 score

**indicator_snapshot** - Tabela z historycznymi snapshotami wskaźników

### Proces ETL

Moduł `python/etl/calc_accum.py` odpowiada za:
- Inkrementalne updaty snapshots wskaźników
- Wywołanie stored procedures dla kalkulacji
- Logging i monitoring procesu


## Database Management

### Struktura schematów

- **raw** - Surowe dane z zewnętrznych źródeł
- **trans** - Dane transakcyjne (quotes, session calendar)
- **at** - Analiza techniczna (widoki, snapshots)

### Komendy migracji

```bash
# Zastosuj wszystkie oczekujące migracje
yoyo apply --config yoyo.ini

# Cofnij ostatnią migrację
yoyo rollback

# Sprawdź status migracji
yoyo list

# Utwórz nową migrację
yoyo new -m "Opis zmian"
```

### Kluczowe tabele

**at.users** - Użytkownicy systemu:
- `id` - Primary key
- `username` - Unikalna nazwa użytkownika
- `password_hash` - Zahashowane hasło
- `email` - Adres email
- `is_active` - Status aktywności
- `created_at`, `updated_at` - Timestampy

**trans.br_quotes** - Notowania giełdowe:
- `oid` - Object ID (identyfikator instrumentu)
- `ts_dt` - Timestamp notowania
- `open`, `high`, `low`, `close` - OHLC
- `volume`, `amount` - Wolumen i wartość
- `grain` - Interwał (1m, 5m, 1h, etc.)

**at.indicator_snapshot** - Snapshoty wskaźników:
- `oid` - Identyfikator instrumentu
- `ts` - Timestamp snapshotu
- `indicator_name` - Nazwa wskaźnika
- `values` - JSONB z wartościami wskaźników

## Development

### Code Quality

Formatowanie kodem Black:
```bash
black .
```

Linting z Flake8:
```bash
flake8 .
```

Type checking z MyPy:
```bash
mypy .
```

### Watch mode dla testów
```bash
pytest --watch
# lub
ptw
```

## Integracja z AIvestor

Moduł 10x-AT integruje się z platformą AIvestor poprzez:
- Wspólną bazę danych PostgreSQL
- Zunifikowany model danych dla instrumentów finansowych
- Współdzielone mechanizmy autentykacji


## Contributing

Projekt jest częścią ekosystemu [AIvestor.pl](https://aivestor.pl) i [10xDevs.pl](https://10xdevs.pl).

## License

ISC
