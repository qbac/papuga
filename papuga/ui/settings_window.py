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
from papuga import config as cfg
from papuga import hotkey as hk
from papuga.tts.edge_engine import POLISH_VOICES as EDGE_VOICES
from papuga.tts.piper_engine import POLISH_VOICES as PIPER_VOICES

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

ENGINE_LABELS = {
    "Edge TTS (online, naturalny głos)": "edge",
    "Piper (offline, lokalny)": "piper",
    "API (ElevenLabs / OpenAI / inny)": "api",
}
ENGINE_LABELS_REV = {v: k for k, v in ENGINE_LABELS.items()}


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
    win.title("Papuga — ustawienia")
    win.geometry("480x710")
    win.resizable(False, False)

    pad = {"padx": 20, "pady": (8, 0)}

    ctk.CTkLabel(win, text="Papuga", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(18, 0))
    ctk.CTkLabel(win, text="Zaznacz tekst, wciśnij skrót, posłuchaj.", text_color="gray").pack(pady=(0, 12))

    # --- Silnik -----------------------------------------------------
    ctk.CTkLabel(win, text="Silnik mowy", anchor="w").pack(fill="x", **pad)
    engine_var = ctk.StringVar(master=win, value=ENGINE_LABELS_REV.get(settings.engine, list(ENGINE_LABELS)[0]))
    engine_menu = ctk.CTkOptionMenu(win, values=list(ENGINE_LABELS.keys()), variable=engine_var)
    engine_menu.pack(fill="x", padx=20, pady=(4, 0))

    # --- Kontener na ustawienia zależne od silnika -------------------
    dynamic_frame = ctk.CTkFrame(win, fg_color="transparent")
    dynamic_frame.pack(fill="x", padx=20, pady=(10, 0))

    edge_voice_var = ctk.StringVar(master=win, value=settings.edge_voice)
    piper_voice_var = ctk.StringVar(master=win, value=settings.piper_voice_id)
    api_provider_var = ctk.StringVar(master=win, value=settings.api_provider)
    api_base_url_var = ctk.StringVar(master=win, value=settings.api_base_url)
    api_key_var = ctk.StringVar(master=win, value=settings.api_key)
    api_model_var = ctk.StringVar(master=win, value=settings.api_model)
    api_voice_var = ctk.StringVar(master=win, value=settings.api_voice)

    def render_dynamic_section() -> None:
        for child in dynamic_frame.winfo_children():
            child.destroy()

        engine_key = ENGINE_LABELS[engine_var.get()]

        if engine_key == "edge":
            ctk.CTkLabel(dynamic_frame, text="Głos", anchor="w").pack(fill="x")
            ctk.CTkOptionMenu(dynamic_frame, values=EDGE_VOICES, variable=edge_voice_var).pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(
                dynamic_frame,
                text="Wymaga internetu. Darmowe, bardzo naturalne głosy Microsoft.",
                text_color="gray", wraplength=420, justify="left",
            ).pack(fill="x", pady=(6, 0))

        elif engine_key == "piper":
            ctk.CTkLabel(dynamic_frame, text="Głos", anchor="w").pack(fill="x")
            ctk.CTkOptionMenu(dynamic_frame, values=list(PIPER_VOICES), variable=piper_voice_var).pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(
                dynamic_frame,
                text="W pełni offline. Model głosu pobiera się jednorazowo (~60 MB) przy pierwszym użyciu.",
                text_color="gray", wraplength=420, justify="left",
            ).pack(fill="x", pady=(6, 0))

        else:  # api
            ctk.CTkLabel(dynamic_frame, text="Dostawca", anchor="w").pack(fill="x")
            ctk.CTkOptionMenu(
                dynamic_frame, values=["openai", "elevenlabs", "custom"], variable=api_provider_var
            ).pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(dynamic_frame, text="Adres API (base URL)", anchor="w").pack(fill="x", pady=(8, 0))
            ctk.CTkEntry(dynamic_frame, textvariable=api_base_url_var).pack(fill="x", pady=(4, 0))

            ctk.CTkLabel(dynamic_frame, text="Klucz API", anchor="w").pack(fill="x", pady=(8, 0))
            ctk.CTkEntry(dynamic_frame, textvariable=api_key_var, show="•").pack(fill="x", pady=(4, 0))

            row = ctk.CTkFrame(dynamic_frame, fg_color="transparent")
            row.pack(fill="x", pady=(8, 0))
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=(0, 6))
            right = ctk.CTkFrame(row, fg_color="transparent")
            right.pack(side="left", fill="x", expand=True, padx=(6, 0))
            ctk.CTkLabel(left, text="Model", anchor="w").pack(fill="x")
            ctk.CTkEntry(left, textvariable=api_model_var).pack(fill="x", pady=(4, 0))
            ctk.CTkLabel(right, text="Głos", anchor="w").pack(fill="x")
            ctk.CTkEntry(right, textvariable=api_voice_var).pack(fill="x", pady=(4, 0))

    engine_menu.configure(command=lambda _v: render_dynamic_section())
    render_dynamic_section()

    # --- Skróty klawiszowe -------------------------------------------
    ctk.CTkLabel(win, text="Skróty klawiszowe", anchor="w").pack(fill="x", **pad)

    hk_row = ctk.CTkFrame(win, fg_color="transparent")
    hk_row.pack(fill="x", padx=20, pady=(4, 0))
    hk_left = ctk.CTkFrame(hk_row, fg_color="transparent")
    hk_left.pack(side="left", fill="x", expand=True, padx=(0, 6))
    hk_right = ctk.CTkFrame(hk_row, fg_color="transparent")
    hk_right.pack(side="left", fill="x", expand=True, padx=(6, 0))

    read_hotkey_var = ctk.StringVar(master=win, value=settings.hotkey_read)
    stop_hotkey_var = ctk.StringVar(master=win, value=settings.hotkey_stop)

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
                status_label.configure(text=capture.error)
            held = capture.preview
            button.configure(text=f"{held} + …" if held else "Naciśnij skrót…  (Esc = anuluj)")
            win.after(50, poll)

        def start_capture() -> None:
            if capture_state["capture"] is not None:
                return
            app.hotkeys.stop()  # inaczej wciśnięty skrót odpaliłby czytanie
            capture = hk.HotkeyCapture()
            capture_state["capture"] = capture
            capture_state["button"] = button
            capture.start()
            button.configure(text="Naciśnij skrót…  (Esc = anuluj)")
            status_label.configure(text="")
            poll()

        button.configure(command=start_capture)
        return button

    ctk.CTkLabel(hk_left, text="Czytaj", anchor="w").pack(fill="x")
    make_recorder(hk_left, read_hotkey_var).pack(fill="x", pady=(4, 0))
    ctk.CTkLabel(hk_right, text="Zatrzymaj", anchor="w").pack(fill="x")
    make_recorder(hk_right, stop_hotkey_var).pack(fill="x", pady=(4, 0))

    ctk.CTkLabel(
        win,
        text="Kliknij pole i wciśnij kombinację klawiszy (może zawierać Win).\n"
             "Uwaga: skróty systemowe Windows (np. Win+R, Win+E) zostaną otwarte przez system.",
        text_color="gray", font=ctk.CTkFont(size=11), justify="left", wraplength=440,
    ).pack(fill="x", padx=20, pady=(4, 0))

    # --- Prędkość mowy -------------------------------------------------
    ctk.CTkLabel(win, text="Prędkość mowy", anchor="w").pack(fill="x", **pad)
    speed_var = ctk.DoubleVar(master=win, value=settings.speed)
    speed_label = ctk.CTkLabel(win, text=f"{settings.speed:.2f}x")

    def on_speed_change(value) -> None:
        speed_label.configure(text=f"{float(value):.2f}x")

    speed_row = ctk.CTkFrame(win, fg_color="transparent")
    speed_row.pack(fill="x", padx=20, pady=(4, 0))
    ctk.CTkSlider(
        speed_row, from_=0.5, to=2.0, variable=speed_var, command=on_speed_change
    ).pack(side="left", fill="x", expand=True)
    speed_label.pack(in_=speed_row, side="left", padx=(10, 0))

    # --- Status / błędy ------------------------------------------------
    status_label = ctk.CTkLabel(win, text="", text_color="#c62828")
    status_label.pack(fill="x", padx=20, pady=(10, 0))

    # --- Stopka: wersja + autor ------------------------------------------
    # Pakowana PRZED przyciskami (side="bottom"), żeby lądowała pod nimi.
    footer = ctk.CTkFrame(win, fg_color="transparent")
    footer.pack(fill="x", padx=20, pady=(0, 10), side="bottom")
    ctk.CTkLabel(
        footer, text=f"{APP_NAME} v{__version__}  ·  autor:", text_color="gray",
        font=ctk.CTkFont(size=11),
    ).pack(side="left")
    author_link = ctk.CTkLabel(
        footer, text=f"@{AUTHOR} na GitHubie", text_color=("#1a73e8", "#6ea8fe"),
        font=ctk.CTkFont(size=11, underline=True), cursor="hand2",
    )
    author_link.pack(side="left", padx=(4, 0))
    author_link.bind("<Button-1>", lambda _e: webbrowser.open(AUTHOR_URL))

    # --- Przyciski -------------------------------------------------------
    btn_row = ctk.CTkFrame(win, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=18, side="bottom")

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
        new_settings = cfg.Settings(
            engine=ENGINE_LABELS[engine_var.get()],
            hotkey_read=read_hotkey_var.get().strip(),
            hotkey_stop=stop_hotkey_var.get().strip(),
            speed=round(speed_var.get(), 2),
            start_with_system=settings.start_with_system,
            edge_voice=edge_voice_var.get(),
            piper_voice_id=piper_voice_var.get(),
            piper_model_path=settings.piper_model_path,
            piper_config_path=settings.piper_config_path,
            api_provider=api_provider_var.get(),
            api_base_url=api_base_url_var.get().strip(),
            api_key=api_key_var.get().strip(),
            api_model=api_model_var.get().strip(),
            api_voice=api_voice_var.get().strip(),
        )
        if not new_settings.hotkey_read or not new_settings.hotkey_stop:
            status_label.configure(text="Uzupełnij oba skróty klawiszowe.")
            return
        if new_settings.hotkey_read == new_settings.hotkey_stop:
            status_label.configure(text="Skróty „Czytaj” i „Zatrzymaj” muszą się różnić.")
            return
        cfg.save(new_settings)
        try:
            app.reload_settings()
        except Exception as exc:  # noqa: BLE001
            status_label.configure(text=f"Zapisano, ale skróty nie zadziałały: {exc}")
            return
        win.destroy()

    ctk.CTkButton(btn_row, text="Zapisz", command=do_save).pack(side="right")
    ctk.CTkButton(
        btn_row, text="Anuluj", fg_color="transparent", border_width=1, command=close
    ).pack(side="right", padx=(0, 10))
    win.protocol("WM_DELETE_WINDOW", close)

    win.mainloop()

