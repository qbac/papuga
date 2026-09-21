# Papuga 🦜

[![Najnowsze wydanie](https://img.shields.io/github/v/release/qbac/papuga?label=wydanie)](https://github.com/qbac/papuga/releases/latest)
[![Licencja: GPL v3](https://img.shields.io/badge/licencja-GPL--3.0-blue.svg)](LICENSE)

[English](README.md) · **Polski**

Zaznacz tekst gdziekolwiek na komputerze, wciśnij skrót klawiszowy i posłuchaj.
Papuga siedzi w zasobniku systemowym, czyta w **80 językach** i — jeśli chcesz — działa **w pełni offline**.

## Pobieranie (Windows)

Pobierz **`Papuga-vX.Y.Z-windows-x64.exe`** z
[najnowszego wydania](https://github.com/qbac/papuga/releases/latest). To jeden
samodzielny plik: bez instalacji, bez Pythona, bez dodatkowej konfiguracji. Uruchom, a ikona
pojawi się w zasobniku systemowym (może być schowana pod strzałką „pokaż ukryte ikony”).

Obok pliku leży suma kontrolna `.sha256`:

```powershell
Get-FileHash .\Papuga-v0.2.0-windows-x64.exe -Algorithm SHA256
```

> **Windows SmartScreen** może ostrzec przed „nieznanym wydawcą”, bo plik nie jest podpisany
> certyfikatem. Wybierz *Więcej informacji → Uruchom mimo to*. Kod źródłowy jest w tym
> repozytorium, a plik buduje publiczny workflow ([`release.yml`](.github/workflows/release.yml)).

## Jak to działa

1. Zaznaczasz dowolny tekst — w przeglądarce, Wordzie, PDF-ie, mailu, gdziekolwiek.
2. Wciskasz globalny skrót (domyślnie **Ctrl+Alt+R**).
3. Papuga kopiuje zaznaczenie, zamienia je na mowę i odtwarza. Długie teksty są dzielone na
   zdania: mowa rusza po pierwszym, a resztę Papuga generuje w tle w trakcie czytania.
4. **Ctrl+Alt+S** (domyślnie) przerywa czytanie w dowolnym momencie.

Ikona w trayu zmienia kolor: zielona = gotowa, pomarańczowa = czyta, czerwona = błąd.

## Języki (świetne do nauki języków)

W ustawieniach wybierasz **język czytania** — hiszpański, francuski, niemiecki, angielski,
japoński, polski i ok. 70 kolejnych — a Papuga czyta zaznaczony tekst głosem dla tego języka.
Uczysz się języka? Kliknij prawym na ikonę w trayu → **Język czytania**, żeby przełączać się
między najczęściej używanymi językami bez otwierania ustawień.

Lista języków i głosów zależy od silnika:

| Silnik | Offline? | Języki / głosy | Uwagi |
|---|---|---|---|
| **Edge TTS** (domyślny) | Nie (potrzebuje internetu) | 75 języków, 300+ naturalnych głosów | Część głosów jest wielojęzyczna. Za darmo, bez klucza. |
| **Piper** | **Tak, w 100%** | 49 języków, 170 głosów | Wbudowany. Wybrany głos pobiera się raz (~60 MB) przy pierwszym użyciu, potem działa offline. |
| **API** | Nie | Zależnie od dostawcy | Endpointy OpenAI-compatible, ElevenLabs, własny URL. Wymaga własnego klucza API. |

> Ustawienia pokazują tylko języki, dla których wybrany silnik ma głosy. Jeśli przełączysz
> się na silnik, który nie obsługuje Twojego obecnego języka, Papuga wybierze angielski.

## Ustawienia

Prawy klik na ikonę trayu → *Ustawienia...*:

- silnik mowy, język czytania i głos,
- oba skróty klawiszowe — kliknij pole i **wciśnij wybraną kombinację** (nic nie trzeba
  wpisywać); można użyć klawisza **Windows**, Esc anuluje. Skróty zarezerwowane przez
  Windows (np. Win+R) i tak obsłuży system,
- prędkość mowy (0.5×–2.0×),
- język interfejsu (angielski lub polski; „Automatyczny” podąża za językiem systemu).

Konfiguracja zapisuje się automatycznie (`%APPDATA%\Papuga\config.json`). Logi:
`%LOCALAPPDATA%\Papuga\Logs\papuga.log`. Pobrane głosy Pipera:
`%LOCALAPPDATA%\Papuga\piper_voices`.

### Autostart z systemem Windows

`Win+R` → `shell:startup` → wrzuć tam skrót do `Papuga.exe`.

## Uruchomienie ze źródeł

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

Gotowe wydania są obecnie budowane tylko dla Windows. Na Linuksie uruchamiaj ze źródeł lub
zbuduj samodzielnie (`./scripts/build_linux.sh` → `dist/Papuga`; bez automatycznych wydań).

## Budowanie .exe lokalnie (Windows)

```powershell
.\scripts\build_windows.ps1
```

Wynik: `dist\Papuga.exe` — jeden plik. Buduj na Windowsie (PyInstaller nie kompiluje
krzyżowo). `Papuga.exe --selftest` sprawdza zbudowany plik: syntezuje mowę Piperem, otwiera
okno Tk i wczytuje katalog głosów (wynik w logu i w kodzie wyjścia).

## Wersjonowanie i wydania

Wersja aplikacji ma jedno źródło prawdy: `__version__` w
[`papuga/__init__.py`](papuga/__init__.py) ([SemVer](https://semver.org/lang/pl/)). Wydanie:

```bash
# 1. podbij __version__ w papuga/__init__.py i zacommituj
# 2. oznacz commit tagiem zgodnym z wersją i wypchnij
git tag v0.3.0
git push origin v0.3.0
```

Workflow [`release.yml`](.github/workflows/release.yml) sprawdzi, czy tag zgadza się z
`__version__`, zbuduje `Papuga.exe` na Windowsie, uruchomi samotest i opublikuje plik w
*Releases* z sumą SHA-256 oraz automatycznymi notatkami wydania.

## Licencja

Papuga jest wolnym oprogramowaniem na licencji **[GNU GPL v3 lub nowszej](LICENSE)** © 2026
[qbac](https://github.com/qbac). Zawiera [Piper](https://github.com/OHF-Voice/piper1-gpl)
(GPL-3.0-or-later), dlatego cały program jest na GPL. Wszystkie komponenty oraz **licencje
głosów** opisuje [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) — każdy głos Pipera ma własną
licencję, a Edge TTS to nieoficjalny klient usługi Microsoftu (Papuga nie jest z Microsoftem
powiązana).
