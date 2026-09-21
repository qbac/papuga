"""
Okno ustawień Papugi — proste, czytelne GUI oparte o customtkinter.
Uruchamiane w osobnym wątku z tray'a; działa na własnym, niezależnym
oknie Tk, więc nie koliduje z pętlą ikony w zasobniku.
"""
from __future__ import annotations

import gc
import webbrowser

import customtkinter as ctk

from papuga import APP_NAME, AUTHOR, AUTHOR_URL, __version__
from papuga import autostart
from papuga import config as cfg
from papuga import hotkey as hk
from papuga import i18n, voices
from papuga.i18n import t

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

ENGINE_KEYS = ("edge", "piper", "api")


def open_settings_window(app) -> None:
    try:
        _run_settings_window(app)
    finally:
        # Zmienne Tk muszą zginąć w wątku, który je utworzył — inaczej ich __del__
        # odpali w cudzym wątku i zawiesi kolejne otwarcie okna ustawień.
        gc.collect()


def _run_settings_window(app) -> None:
    settings = cfg.load()

    win = ctk.CTk()
    win.title(t("settings_title"))
    win.geometry("500x700")
    win.minsize(480, 520)

    pad = {"padx": 4, "pady": (10, 0)}

    # --- Dolny pasek (pakowany PRZED treścią, żeby zawsze był widoczny) ---
    footer = ctk.CTkFrame(win, fg_color="transparent")
    footer.pack(fill="x", padx=20, pady=(0, 10), side="bottom")
    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=(6, 8), side="bottom")
    status_label = ctk.CTkLabel(win, text="", text_color="#c62828", wraplength=450, justify="left")
    status_label.pack(fill="x", padx=24, side="bottom")

    scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=(12, 8), pady=(8, 0))

    def update_scrollbar(_event=None) -> None:
        """Pasek przewijania tylko wtedy, gdy zawartość nie mieści się w oknie."""
        try:
            canvas = scroll._parent_canvas
            bbox = canvas.bbox("all")
            overflow = bool(bbox) and (bbox[3] - bbox[1]) > canvas.winfo_height() + 1
            if overflow:
                scroll._scrollbar.grid()
            else:
                scroll._scrollbar.grid_remove()
        except Exception:  # noqa: BLE001 — wnętrze customtkinter; w razie zmian zostaw domyślny pasek
            pass

    # Zawartość zmienia wysokość (np. po zmianie silnika), okno zmienia rozmiar — sprawdzaj oba.
    scroll.bind("<Configure>", lambda _e: win.after_idle(update_scrollbar), add="+")
    scroll._parent_canvas.bind("<Configure>", lambda _e: win.after_idle(update_scrollbar), add="+")

    ctk.CTkLabel(scroll, text="Papuga", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(4, 0))
    ctk.CTkLabel(scroll, text=t("tagline"), text_color="gray").pack(pady=(0, 6))

    # --- Zmienne (zawsze z master=win) --------------------------------
    engine_labels = {
        "edge": t("engine_edge"), "piper": t("engine_piper"), "api": t("engine_api"),
    }
    engine_by_label = {v: k for k, v in engine_labels.items()}
    engine_var = ctk.StringVar(master=win, value=engine_labels.get(settings.engine, engine_labels["edge"]))
    language_var = ctk.StringVar(master=win, value="")
    edge_voice_var = ctk.StringVar(master=win, value="")
    piper_voice_var = ctk.StringVar(master=win, value="")
    api_provider_var = ctk.StringVar(master=win, value=settings.api_provider)
    api_base_url_var = ctk.StringVar(master=win, value=settings.api_base_url)
    api_key_var = ctk.StringVar(master=win, value=settings.api_key)
    api_model_var = ctk.StringVar(master=win, value=settings.api_model)
    api_voice_var = ctk.StringVar(master=win, value=settings.api_voice)
    read_hotkey_var = ctk.StringVar(master=win, value=settings.hotkey_read)
    stop_hotkey_var = ctk.StringVar(master=win, value=settings.hotkey_stop)
    speed_var = ctk.DoubleVar(master=win, value=settings.speed)
    ui_labels = {"auto": t("ui_auto"), **i18n.UI_LANGUAGES}
    ui_by_label = {v: k for k, v in ui_labels.items()}
    ui_var = ctk.StringVar(master=win, value=ui_labels.get(settings.ui_language, ui_labels["auto"]))

    # Stan wyboru: język + identyfikatory głosów (zmienne trzymają etykiety do wyświetlenia).
    state = {
        "lang": settings.language,
        "edge_voice": settings.edge_voice,
        "piper_voice": settings.piper_voice_id,
    }
    label_maps: dict[str, dict[str, str]] = {"edge": {}, "piper": {}}

    def engine_key() -> str:
        return engine_by_label.get(engine_var.get(), "edge")

    def languages_for(engine: str) -> list[str]:
        codes = voices.language_codes()
        if engine == "edge":
            return [c for c in codes if voices.edge_voices(c)]
        if engine == "piper":
            return [c for c in codes if voices.piper_voices(c)]
        return codes

    def voice_options(engine: str, lang: str) -> tuple[list[str], dict[str, str]]:
        """Etykiety do listy + mapa etykieta -> id głosu."""
        if engine == "edge":
            items = [(voices.edge_voice_label(v), v["id"]) for v in voices.edge_voices(lang)]
        else:
            items = [(voices.piper_voice_label(v), v["id"]) for v in voices.piper_voices(lang)]
        return [label for label, _ in items], dict(items)

    def label_for_voice(engine: str, lang: str, voice_id: str) -> str:
        labels, mapping = voice_options(engine, lang)
        for label, vid in mapping.items():
            if vid == voice_id:
                return label
        return labels[0] if labels else ""

    def sync_voice_vars() -> None:
        """Ustawia etykiety w zmiennych głosów wg stanu (po zmianie języka)."""
        lang = state["lang"]
        edge_voice_var.set(label_for_voice("edge", lang, state["edge_voice"]))
        piper_voice_var.set(label_for_voice("piper", lang, state["piper_voice"]))

    # --- Silnik --------------------------------------------------------
    ctk.CTkLabel(scroll, text=t("engine"), anchor="w").pack(fill="x", **pad)
    engine_menu = ctk.CTkOptionMenu(scroll, values=list(engine_labels.values()), variable=engine_var)
    engine_menu.pack(fill="x", padx=4, pady=(4, 0))

    # --- Język czytania ------------------------------------------------
    ctk.CTkLabel(scroll, text=t("language"), anchor="w").pack(fill="x", **pad)
    lang_menu = ctk.CTkOptionMenu(scroll, values=[""], variable=language_var)
    lang_menu.pack(fill="x", padx=4, pady=(4, 0))

    # --- Kontener na ustawienia zależne od silnika ---------------------
    dynamic_frame = ctk.CTkFrame(scroll, fg_color="transparent")
    dynamic_frame.pack(fill="x", padx=4, pady=(6, 0))

    def render_dynamic_section() -> None:
        for child in dynamic_frame.winfo_children():
            child.destroy()

        engine = engine_key()
        lang = state["lang"]

        if engine in ("edge", "piper"):
            labels, mapping = voice_options(engine, lang)
            label_maps[engine] = mapping
            var = edge_voice_var if engine == "edge" else piper_voice_var
            ctk.CTkLabel(dynamic_frame, text=t("voice"), anchor="w").pack(fill="x")
            menu = ctk.CTkOptionMenu(dynamic_frame, values=labels or [""], variable=var)
            menu.pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(
                dynamic_frame,
                text=t("edge_note" if engine == "edge" else "piper_note"),
                text_color="gray", wraplength=430, justify="left",
            ).pack(fill="x", pady=(6, 0))

        else:  # api
            ctk.CTkLabel(dynamic_frame, text=t("provider"), anchor="w").pack(fill="x")
            ctk.CTkOptionMenu(
                dynamic_frame, values=["openai", "elevenlabs", "custom"], variable=api_provider_var
            ).pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(dynamic_frame, text=t("base_url"), anchor="w").pack(fill="x", pady=(8, 0))
            ctk.CTkEntry(dynamic_frame, textvariable=api_base_url_var).pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(dynamic_frame, text=t("api_key"), anchor="w").pack(fill="x", pady=(8, 0))
            ctk.CTkEntry(dynamic_frame, textvariable=api_key_var, show="•").pack(fill="x", pady=(4, 0))

            row = ctk.CTkFrame(dynamic_frame, fg_color="transparent")
            row.pack(fill="x", pady=(8, 0))
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=(0, 6))
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="left", fill="x", expand=True, padx=(6, 0))
            ctk.CTkLabel(left, text=t("model"), anchor="w").pack(fill="x")
            ctk.CTkEntry(left, textvariable=api_model_var).pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(right, text=t("voice"), anchor="w").pack(fill="x")
            ctk.CTkEntry(right, textvariable=api_voice_var).pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(
                dynamic_frame, text=t("api_note"), text_color="gray", wraplength=430, justify="left",
            ).pack(fill="x", pady=(6, 0))

    def refresh_language_menu() -> None:
        """Lista języków zależy od silnika (nie każdy silnik ma głosy w każdym języku)."""
        engine = engine_key()
        codes = languages_for(engine)
        if engine != "api" and state["lang"] not in codes:
            state["lang"] = "en" if "en" in codes else (codes[0] if codes else state["lang"])
            state["edge_voice"] = voices.default_edge_voice(state["lang"])
            state["piper_voice"] = voices.default_piper_voice(state["lang"])
        labels = [voices.language_label(c) for c in codes]
        lang_menu.configure(values=labels or [""], state="disabled" if engine == "api" else "normal")
        language_var.set(voices.language_label(state["lang"]))
        sync_voice_vars()

    fit_window_hook: dict = {"fn": None}  # ustawiane na końcu (fit_window powstaje po zbudowaniu UI)

    def on_engine_change(_value) -> None:
        refresh_language_menu()
        render_dynamic_section()
        if fit_window_hook["fn"]:  # silnik API ma więcej pól — okno może urosnąć, nie kurczy się
            win.after_idle(lambda: fit_window_hook["fn"](grow_only=True))

    def on_language_change(label: str) -> None:
        by_label = {voices.language_label(c): c for c in languages_for(engine_key())}
        code = by_label.get(label)
        if not code:
            return
        state["lang"] = code
        state["edge_voice"] = voices.default_edge_voice(code)
        state["piper_voice"] = voices.default_piper_voice(code)
        sync_voice_vars()
        render_dynamic_section()

    engine_menu.configure(command=on_engine_change)
    lang_menu.configure(command=on_language_change)
    refresh_language_menu()
    render_dynamic_section()

    # --- Skróty klawiszowe -------------------------------------------
    ctk.CTkLabel(scroll, text=t("hotkeys"), anchor="w").pack(fill="x", **pad)

    hk_row = ctk.CTkFrame(scroll, fg_color="transparent")
    hk_row.pack(fill="x", padx=4, pady=(4, 0))
    hk_left = ctk.CTkFrame(hk_row, fg_color="transparent")
    hk_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
    hk_right = ctk.CTkFrame(hk_row, fg_color="transparent")
    hk_right.pack(side="left", fill="x", expand=True, padx=(6, 0))

    capture_state: dict = {"capture": None}

    def make_recorder(parent, var: ctk.StringVar) -> ctk.CTkButton:
        """Przycisk: klik -> wciśnij kombinację -> zapisuje ją w `var`."""
        button = ctk.CTkButton(
            parent, text=hk.prettify(var.get()), fg_color=("gray85", "gray25"),
            text_color=("gray10", "gray90"), hover_color=("gray75", "gray35"),
        )

        def poll() -> None:
            capture = capture_state["capture"]
            if capture is None or capture_state.get("button") is not button:
                return
            if capture.done:
                capture.stop()
                capture_state["capture"] = None
                if capture.result:
                    var.set(capture.result)
                    status_label.configure(text="")
                button.configure(text=hk.prettify(var.get()))
                app._register_hotkeys()  # skróty były wstrzymane na czas nagrywania
                return
            if capture.error:
                status_label.configure(text=t(capture.error))
            held = capture.preview
            button.configure(text=f"{held} + …" if held else t("press_hotkey"))
            win.after(50, poll)

        def start_capture() -> None:
            if capture_state["capture"] is not None:
                return
            app.hotkeys.stop()  # inaczej wciśnięty skrót odpaliłby czytanie
            capture = hk.HotkeyCapture()
            capture_state["capture"] = capture
            capture_state["button"] = button
            capture.start()
            button.configure(text=t("press_hotkey"))
            status_label.configure(text="")
            poll()

        button.configure(command=start_capture)
        return button

    ctk.CTkLabel(hk_left, text=t("read"), anchor="w").pack(fill="x")
    make_recorder(hk_left, read_hotkey_var).pack(fill="x", pady=(4, 0))
    ctk.CTkLabel(hk_right, text=t("stop"), anchor="w").pack(fill="x")
    make_recorder(hk_right, stop_hotkey_var).pack(fill="x", pady=(4, 0))

    ctk.CTkLabel(
        scroll, text=t("hotkey_hint"),
        text_color="gray", font=ctk.CTkFont(size=11), justify="left", wraplength=430,
    ).pack(fill="x", padx=4, pady=(4, 0))

    # --- Prędkość mowy -------------------------------------------------
    # Nagłówek z bieżącą wartością (wartość obok suwaka byłaby wypychana poza okno).
    speed_header = ctk.CTkFrame(scroll, fg_color="transparent")
    speed_header.pack(fill="x", padx=4, pady=(10, 0))
    speed_label = ctk.CTkLabel(
        speed_header, text=f"{settings.speed:.2f}x", font=ctk.CTkFont(weight="bold")
    )
    speed_label.pack(side="right")
    ctk.CTkLabel(speed_header, text=t("speed"), anchor="w").pack(side="left")

    def on_speed_change(value) -> None:
        speed_label.configure(text=f"{float(value):.2f}x")

    ctk.CTkSlider(
        scroll, from_=0.5, to=2.0, number_of_steps=30,  # kroki co 0,05x
        variable=speed_var, command=on_speed_change,
    ).pack(fill="x", padx=4, pady=(6, 0))

    # --- Autostart: jeden przycisk dodaje/usuwa, działa od razu (bez „Zapisz”) ---
    if autostart.supported():
        auto_row = ctk.CTkFrame(scroll, fg_color="transparent")
        auto_row.pack(fill="x", padx=4, pady=(14, 0))
        auto_status = ctk.CTkLabel(auto_row, text="", anchor="w")
        auto_status.pack(side="left")
        auto_button = ctk.CTkButton(auto_row, text="", width=180)
        auto_button.pack(side="right")

        def refresh_autostart() -> None:
            on = autostart.is_enabled()
            auto_status.configure(
                text=f"{t('autostart')}: {t('autostart_on' if on else 'autostart_off')}"
            )
            auto_button.configure(text=t("autostart_remove" if on else "autostart_add"))

        def toggle_autostart() -> None:
            try:
                autostart.set_enabled(not autostart.is_enabled())
                status_label.configure(text="")
            except OSError as exc:
                status_label.configure(text=t("autostart_failed", error=exc))
            refresh_autostart()

        auto_button.configure(command=toggle_autostart)
        refresh_autostart()

    # --- Język interfejsu ------------------------------------------------
    ctk.CTkLabel(scroll, text=t("ui_language"), anchor="w").pack(fill="x", **pad)
    ctk.CTkOptionMenu(scroll, values=list(ui_labels.values()), variable=ui_var).pack(
        fill="x", padx=4, pady=(4, 8)
    )

    # --- Stopka: wersja + autor ------------------------------------------
    ctk.CTkLabel(
        footer, text=f"{APP_NAME} v{__version__}  ·  {t('author')}", text_color="gray",
        font=ctk.CTkFont(size=11),
    ).pack(side="left")
    author_link = ctk.CTkLabel(
        footer, text=t("author_link", author=AUTHOR), text_color=("#1a73e8", "#6ea8fe"),
        font=ctk.CTkFont(size=11, underline=True), cursor="hand2",
    )
    author_link.pack(side="left", padx=(4, 0))
    author_link.bind("<Button-1>", lambda _e: webbrowser.open(AUTHOR_URL))

    # --- Przyciski -------------------------------------------------------
    def close() -> None:
        capture = capture_state["capture"]
        if capture is not None:
            capture.stop()
            capture_state["capture"] = None
            app._register_hotkeys()
        win.destroy()

    def do_save() -> None:
        capture = capture_state["capture"]
        if capture is not None:  # zapis w trakcie nagrywania skrótu — porzuć nagrywanie
            capture.stop()
            capture_state["capture"] = None

        lang = state["lang"]
        edge_id = label_maps["edge"].get(edge_voice_var.get(), state["edge_voice"])
        piper_id = label_maps["piper"].get(piper_voice_var.get(), state["piper_voice"])
        new_settings = cfg.Settings(
            engine=engine_key(),
            language=lang,
            ui_language=ui_by_label.get(ui_var.get(), "auto"),
            recent_languages=([lang] + [c for c in settings.recent_languages if c != lang])[:8],
            hotkey_read=read_hotkey_var.get().strip(),
            hotkey_stop=stop_hotkey_var.get().strip(),
            speed=round(speed_var.get(), 2),
            start_with_system=autostart.is_enabled(),
            edge_voice=edge_id,
            piper_voice_id=piper_id,
            api_provider=api_provider_var.get(),
            api_base_url=api_base_url_var.get().strip(),
            api_key=api_key_var.get().strip(),
            api_model=api_model_var.get().strip(),
            api_voice=api_voice_var.get().strip(),
        )
        if not new_settings.hotkey_read or not new_settings.hotkey_stop:
            status_label.configure(text=t("fill_hotkeys"))
            return
        if new_settings.hotkey_read == new_settings.hotkey_stop:
            status_label.configure(text=t("hotkeys_differ"))
            return
        cfg.save(new_settings)
        try:
            app.reload_settings()
        except Exception as exc:  # noqa: BLE001
            status_label.configure(text=t("saved_hotkeys_failed", error=exc))
            return
        win.destroy()

    ctk.CTkButton(btn_row, text=t("save"), command=do_save).pack(side="right")
    ctk.CTkButton(
        btn_row, text=t("cancel"), fg_color="transparent", border_width=1, command=close
    ).pack(side="right", padx=(0, 10))
    win.protocol("WM_DELETE_WINDOW", close)

    def fit_window(grow_only: bool = False) -> None:
        """Wysokość okna dopasowana do zawartości (max: ekran). Pasek przewijania pokaże się
        dopiero, gdy zawartość naprawdę się nie mieści (np. mały ekran)."""
        try:
            win.update_idletasks()
            factor = win._get_window_scaling()  # CTk skaluje geometry() o DPI
            fixed = footer.winfo_reqheight() + btn_row.winfo_reqheight() + status_label.winfo_reqheight()
            want = (scroll.winfo_reqheight() + fixed + 48) / factor
            limit = (win.winfo_screenheight() - 110) / factor
            height = int(min(want, limit))
            if grow_only:
                height = max(height, int(win.winfo_height() / factor))
            win.geometry(f"500x{height}")
        except Exception:  # noqa: BLE001 — w razie problemu zostaje rozmiar domyślny
            pass

    fit_window()
    fit_window_hook["fn"] = fit_window
    win.mainloop()
