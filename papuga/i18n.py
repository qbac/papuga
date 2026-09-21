"""Tłumaczenia interfejsu Papugi (polski i angielski) + wybór języka interfejsu.

Użycie: `from papuga.i18n import t`, potem `t("save")` lub `t("dl_voice", mb=63)`.
Brakujący klucz w wybranym języku spada na angielski, a potem na sam klucz.
"""
from __future__ import annotations

from papuga import voices

UI_LANGUAGES = {"pl": "Polski", "en": "English"}

_current = "en"

STRINGS: dict[str, dict[str, str]] = {
    "en": {
        # okno ustawień
        "settings_title": "Papuga — settings",
        "tagline": "Select text, press the shortcut, listen.",
        "engine": "Speech engine",
        "engine_edge": "Edge TTS (online, natural voices)",
        "engine_piper": "Piper (offline, built in)",
        "engine_api": "API (ElevenLabs / OpenAI / other)",
        "language": "Reading language",
        "voice": "Voice",
        "edge_note": "Needs internet. Free, very natural Microsoft voices.",
        "piper_note": "Works fully offline. The chosen voice is downloaded once on first use.",
        "api_note": "The provider decides the language; the reading language above is not used.",
        "provider": "Provider",
        "base_url": "API address (base URL)",
        "api_key": "API key",
        "model": "Model",
        "hotkeys": "Keyboard shortcuts",
        "read": "Read",
        "stop": "Stop",
        "hotkey_hint": "Click a field and press the key combination (it may include Win).\n"
                       "Note: Windows system shortcuts (e.g. Win+R, Win+E) will still be handled by the system.",
        "press_hotkey": "Press a shortcut…  (Esc = cancel)",
        "need_modifier": "Add a modifier (Ctrl, Alt, Shift or Win).",
        "speed": "Speech speed",
        "ui_language": "Interface language",
        "ui_auto": "Automatic (system)",
        "autostart": "Start with the system",
        "autostart_on": "on",
        "autostart_off": "off",
        "autostart_add": "Add to startup",
        "autostart_remove": "Remove from startup",
        "autostart_failed": "Could not change the startup setting: {error}",
        "save": "Save",
        "cancel": "Cancel",
        "author": "author:",
        "author_link": "@{author} on GitHub",
        "fill_hotkeys": "Fill in both keyboard shortcuts.",
        "hotkeys_differ": "The “Read” and “Stop” shortcuts must be different.",
        "saved_hotkeys_failed": "Saved, but the shortcuts did not work: {error}",
        # tray i powiadomienia
        "tray_read": "Read selection",
        "tray_stop": "Stop",
        "tray_language": "Reading language",
        "tray_settings": "Settings...",
        "tray_quit": "Quit",
        "no_selection": "No text selected.",
        "hotkeys_register_failed": "Could not register the keyboard shortcuts.",
        "unexpected_error": "An unexpected error occurred. Check the logs.",
        "dl_voice": "Downloading the voice ({mb} MB) — one time only. Reading will start when it is ready.",
        "dl_voice_done": "Voice downloaded.",
        # błędy silników
        "err_edge_failed": "edge-tts: could not generate speech ({error})",
        "err_edge_no_audio": "edge-tts: no audio received (check your internet connection)",
        "err_edge_no_voice": "No Edge TTS voice is available for this language.",
        "err_piper_no_voice": "Piper: there is no offline voice for this language. Pick another language or engine.",
        "err_piper_unknown_voice": "Piper: unknown voice '{voice}'",
        "err_piper_download": "Piper: could not download the voice ({error}). Downloading needs internet once.",
        "err_piper_failed": "Piper: speech generation failed ({error})",
        "err_api_no_key": "API engine: no API key set in the settings",
        "err_api_request": "API engine: request failed ({error})",
        "err_elevenlabs_request": "ElevenLabs: request failed ({error})",
        "err_unknown_engine": "Unknown engine: {engine}",
    },
    "pl": {
        "settings_title": "Papuga — ustawienia",
        "tagline": "Zaznacz tekst, wciśnij skrót, posłuchaj.",
        "engine": "Silnik mowy",
        "engine_edge": "Edge TTS (online, naturalne głosy)",
        "engine_piper": "Piper (offline, wbudowany)",
        "engine_api": "API (ElevenLabs / OpenAI / inny)",
        "language": "Język czytania",
        "voice": "Głos",
        "edge_note": "Wymaga internetu. Darmowe, bardzo naturalne głosy Microsoft.",
        "piper_note": "Działa w pełni offline. Wybrany głos pobiera się jednorazowo przy pierwszym użyciu.",
        "api_note": "Język ustala dostawca; wybrany wyżej język czytania nie jest używany.",
        "provider": "Dostawca",
        "base_url": "Adres API (base URL)",
        "api_key": "Klucz API",
        "model": "Model",
        "hotkeys": "Skróty klawiszowe",
        "read": "Czytaj",
        "stop": "Zatrzymaj",
        "hotkey_hint": "Kliknij pole i wciśnij kombinację klawiszy (może zawierać Win).\n"
                       "Uwaga: skróty systemowe Windows (np. Win+R, Win+E) zostaną otwarte przez system.",
        "press_hotkey": "Naciśnij skrót…  (Esc = anuluj)",
        "need_modifier": "Dodaj modyfikator (Ctrl, Alt, Shift lub Win).",
        "speed": "Prędkość mowy",
        "ui_language": "Język interfejsu",
        "ui_auto": "Automatyczny (systemowy)",
        "autostart": "Uruchamianie z systemem",
        "autostart_on": "włączone",
        "autostart_off": "wyłączone",
        "autostart_add": "Dodaj do autostartu",
        "autostart_remove": "Usuń z autostartu",
        "autostart_failed": "Nie udało się zmienić autostartu: {error}",
        "save": "Zapisz",
        "cancel": "Anuluj",
        "author": "autor:",
        "author_link": "@{author} na GitHubie",
        "fill_hotkeys": "Uzupełnij oba skróty klawiszowe.",
        "hotkeys_differ": "Skróty „Czytaj” i „Zatrzymaj” muszą się różnić.",
        "saved_hotkeys_failed": "Zapisano, ale skróty nie zadziałały: {error}",
        "tray_read": "Czytaj zaznaczenie",
        "tray_stop": "Zatrzymaj",
        "tray_language": "Język czytania",
        "tray_settings": "Ustawienia...",
        "tray_quit": "Zakończ",
        "no_selection": "Nie zaznaczono żadnego tekstu.",
        "hotkeys_register_failed": "Nie udało się zarejestrować skrótów klawiszowych.",
        "unexpected_error": "Wystąpił nieoczekiwany błąd. Sprawdź logi.",
        "dl_voice": "Pobieram głos ({mb} MB) — tylko za pierwszym razem. Czytanie ruszy, gdy będzie gotowy.",
        "dl_voice_done": "Głos pobrany.",
        "err_edge_failed": "edge-tts: nie udało się wygenerować mowy ({error})",
        "err_edge_no_audio": "edge-tts: nie otrzymano audio (sprawdź połączenie z internetem)",
        "err_edge_no_voice": "Brak głosu Edge TTS dla tego języka.",
        "err_piper_no_voice": "Piper: brak głosu offline dla tego języka. Wybierz inny język lub silnik.",
        "err_piper_unknown_voice": "Piper: nieznany głos '{voice}'",
        "err_piper_download": "Piper: nie udało się pobrać głosu ({error}). Pobranie wymaga jednorazowo internetu.",
        "err_piper_failed": "Piper: błąd generowania mowy ({error})",
        "err_api_no_key": "Silnik API: brak klucza API w ustawieniach",
        "err_api_request": "Silnik API: błąd zapytania ({error})",
        "err_elevenlabs_request": "ElevenLabs: błąd zapytania ({error})",
        "err_unknown_engine": "Nieznany silnik: {engine}",
    },
}


def resolve(ui_language: str) -> str:
    """'auto' -> język systemu (pl albo en), inaczej wskazany kod."""
    if ui_language in UI_LANGUAGES:
        return ui_language
    return "pl" if voices.system_language() == "pl" else "en"


def set_language(ui_language: str) -> None:
    global _current
    _current = resolve(ui_language)


def current() -> str:
    return _current


def t(key: str, **kwargs) -> str:
    text = STRINGS.get(_current, {}).get(key) or STRINGS["en"].get(key) or key
    return text.format(**kwargs) if kwargs else text
