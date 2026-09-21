# Papuga 🦜

[![Najnowsze wydanie](https://img.shields.io/github/v/release/qbac/papuga?label=wydanie)](https://github.com/qbac/papuga/releases/latest)
[![Licencja: MIT](https://img.shields.io/badge/licencja-MIT-blue.svg)](LICENSE)

Zaznacz tekst gdziekolwiek w systemie, wciśnij skrót klawiszowy, posłuchaj.
Aplikacja siedzi w zasobniku systemowym (tray) i działa w tle.

## Pobieranie (Windows)

Gotowy plik **`Papuga-vX.Y.Z-windows-x64.exe`** znajdziesz w
[najnowszym wydaniu](https://github.com/qbac/papuga/releases/latest). To jeden
samodzielny plik — nie wymaga instalacji ani Pythona. Pobierz, uruchom, ikona pojawi
się w zasobniku systemowym (może być schowana pod strzałką „pokaż ukryte ikony”).

Obok pliku leży suma kontrolna `.sha256`. Sprawdzisz ją w PowerShellu:

```powershell
Get-FileHash .\Papuga-v0.1.0-windows-x64.exe -Algorithm SHA256
```

> **Windows SmartScreen** może ostrzec przed uruchomieniem („Nieznany wydawca”),
> bo plik nie jest podpisany certyfikatem. Wybierz *Więcej informacji → Uruchom mimo to*.
> Kod źródłowy jest w tym repozytorium, a plik buduje publiczny workflow
> ([`release.yml`](.github/workflows/release.yml)).

Wersja aplikacji (i link do autora) widoczne są w stopce okna ustawień.

## Jak to działa

1. Zaznaczasz dowolny tekst — w przeglądarce, Wordzie, PDF-ie, mailu, gdziekolwiek.
2. Wciskasz globalny skrót (domyślnie **Ctrl+Alt+R**).
3. Papuga kopiuje zaznaczenie, wysyła je do wybranego silnika mowy i odtwarza audio.
   Długie teksty są dzielone na zdania — mowa rusza po wygenerowaniu pierwszego,
   a resztę Papuga generuje w tle w trakcie czytania.
4. **Ctrl+Alt+S** (domyślnie) przerywa czytanie w dowolnym momencie.

Ikona w trayu zmienia kolor: zielona = gotowa, pomarańczowa = czyta, czerwona = błąd
(np. brak internetu przy silniku online).

## Trzy silniki mowy do wyboru

Wybierasz w oknie ustawień (prawy klik na ikonę trayu → *Ustawienia...*):

| Silnik | Offline? | Jakość głosu | Wymaga |
|---|---|---|---|
| **Edge TTS** | Nie (potrzebuje internetu) | Bardzo naturalne głosy Microsoft | nic — działa od razu |
| **Piper** | Tak, w 100% lokalnie | Dobra, lekko syntetyczna | jednorazowe pobranie modelu głosu (~60 MB) oraz program `piper` w PATH (patrz niżej) |
| **API** | Nie | Zależy od dostawcy (ElevenLabs = najlepsza jakość na rynku) | własny klucz API |

Uwaga: mimo nazwy, Edge TTS **nie wymaga** zainstalowanej przeglądarki Microsoft Edge —
to zwykłe zapytania HTTP do publicznego endpointu, więc silnik działa identycznie
na Windows i na Linuksie.

Silnik **API** obsługuje od razu:
- dowolny endpoint kompatybilny z OpenAI `/v1/audio/speech` (w tym lokalne serwery),
- ElevenLabs,
- dowolny inny endpoint OpenAI-compatible pod niestandardowym URL-em (`custom`).

### Piper a gotowy plik .exe

Piper uruchamia zewnętrzny program `piper` (instalowany razem z pakietem `piper-tts`).
Samodzielny `.exe` z wydania go **nie zawiera**, więc żeby używać Pipera, zainstaluj go
osobno i upewnij się, że `piper` jest w `PATH`:

```bash
pip install piper-tts
```

Edge TTS i API działają w `.exe` bez żadnych dodatkowych kroków.

## Ustawienia

Wszystko konfiguruje się w GUI (prawy klik na ikonę trayu → *Ustawienia...*):

- silnik mowy i głos,
- oba skróty klawiszowe — kliknij pole i **wciśnij wybraną kombinację** (nie trzeba nic
  wpisywać); można użyć klawisza **Windows**, Esc anuluje nagrywanie. Skróty zarezerwowane
  przez system (np. Win+R) i tak otworzy Windows,
- prędkość mowy (0.5x–2.0x).

Konfiguracja zapisuje się automatycznie w standardowym katalogu konfiguracyjnym
systemu (np. `%APPDATA%\Papuga\config.json` na Windows). Logi:
`%LOCALAPPDATA%\Papuga\Logs\papuga.log`.

### Autostart z systemem Windows

Najprościej: `Win+R` → `shell:startup` → wrzuć tam skrót do `Papuga.exe`.

## Uruchomienie ze źródeł (tryb deweloperski)

Wymaga Pythona 3.11+.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\run_dev.py
# Linux/macOS:
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python scripts/run_dev.py
```

Na Linuksie do obsługi Pipera potrzebny jest dodatkowo pakiet `espeak-ng`
(silnik fonemizujący tekst przed syntezą):

```bash
sudo apt install espeak-ng   # Debian/Ubuntu
sudo pacman -S espeak-ng     # Arch
```

Gotowe wydania są obecnie budowane tylko dla Windows. Na Linuksie uruchamiaj ze źródeł
lub zbuduj samodzielnie (`./scripts/build_linux.sh` → `dist/Papuga`; ten wariant nie jest
objęty automatycznymi wydaniami).

## Budowanie pliku .exe lokalnie (Windows)

Buduj **na Windowsie** (PyInstaller nie kompiluje krzyżowo między systemami):

```powershell
.\scripts\build_windows.ps1
```

Wynik: `dist\Papuga.exe` — jeden plik, do skopiowania gdziekolwiek.

## Wersjonowanie i wydania

Wersja aplikacji ma jedno źródło prawdy: `__version__` w [`papuga/__init__.py`](papuga/__init__.py)
([SemVer](https://semver.org/lang/pl/)). Wydanie nowej wersji:

```bash
# 1. podbij __version__ w papuga/__init__.py i zacommituj
# 2. oznacz commit tagiem zgodnym z wersją i wypchnij
git tag v0.2.0
git push origin v0.2.0
```

Workflow [`release.yml`](.github/workflows/release.yml) sprawdzi, czy tag zgadza się
z `__version__`, zbuduje `Papuga.exe` na Windowsie i opublikuje go w *Releases* razem
z sumą SHA-256 oraz automatycznymi notatkami wydania.

## Struktura projektu

```
papuga/
  __init__.py       wersja (__version__), nazwa, link do autora i repozytorium
  main.py           punkt wejścia (uruchamia tray)
  app.py            spina hotkey + zaznaczenie + TTS + odtwarzanie + tray
  config.py         wczytywanie/zapis ustawień (JSON)
  selection.py      pobieranie zaznaczonego tekstu (symulacja Ctrl+C)
  hotkey.py         globalne skróty klawiszowe + rejestrator skrótów dla UI (pynput)
  player.py         odtwarzanie audio (pygame)
  singleinstance.py blokada jednej działającej instancji
  tts/
    base.py         wspólny interfejs silników
    edge_engine.py  Microsoft Edge TTS (online, darmowy)
    piper_engine.py Piper (offline, lokalny, ONNX)
    api_engine.py   generyczne API (OpenAI-compatible / ElevenLabs)
  ui/
    settings_window.py  okno ustawień (customtkinter)
scripts/
  generate_icon.py  generuje ikony aplikacji
  build_windows.ps1  buduje Papuga.exe
  build_linux.sh      buduje binarkę na Linux
  run_dev.py          szybkie odpalenie bez pakowania
.github/workflows/
  release.yml       build .exe i publikacja wydania po wypchnięciu tagu vX.Y.Z
papuga.spec         konfiguracja PyInstaller
```

## Dodanie nowego silnika TTS

Każdy silnik implementuje `papuga.tts.base.TTSEngine` (jedna metoda:
`synthesize(text, out_dir, speed) -> Path`). Wystarczy dodać nową klasę
w `papuga/tts/`, zarejestrować ją w `papuga/tts/__init__.py::build_engine()`
i dodać opcję w oknie ustawień.

## Licencja

[MIT](LICENSE) © 2026 [qbac](https://github.com/qbac)
