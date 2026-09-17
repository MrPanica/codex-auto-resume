# -*- coding: utf-8 -*-
"""
Codex Auto-Resume Settings GUI (Native Windows 11 Fluent Dark UI)
100% Solid GDI Dark Theme - Completely immune to GPU/DWM transparency glitches.
"""

import sys
import os
import json
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk

# -------------------------------------------------------------
# Пути к файлам
# -------------------------------------------------------------
USER_PROFILE = os.environ.get("USERPROFILE", r"C:\Users\Artur")
CODEX_DIR = os.path.join(USER_PROFILE, ".codex")
os.makedirs(CODEX_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(CODEX_DIR, "guardian_settings.json")
SESSION_INDEX_FILE = os.path.join(CODEX_DIR, "session_index.jsonl")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_FILE = os.path.join(APP_DIR, "icon.ico")
if not os.path.exists(ICON_FILE):
    ICON_FILE = os.path.join(CODEX_DIR, "icon.ico")

AUTOSTART_VBS = os.path.join(
    os.environ.get("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup\CodexAutoResumeWatchdog.vbs"
)

# -------------------------------------------------------------
# Настройки по умолчанию
# -------------------------------------------------------------
DEFAULT_SETTINGS = {
    "language": "auto",  # "auto", "ru", "en"
    "autostart_windows": True,
    "enable_on_codex_start": True,
    "notify_on_toggle": True,
    "notify_on_resume": False,
    "sound_on_resume": False,
    "retry_pause_seconds": 10.0,
    "post_resume_cooldown": 6.0,
    "poll_interval_seconds": 1.0,
    "max_retries_consecutive": 10,
    "error_patterns": [
        {"pattern": "selected model is at capacity", "name": "Model Capacity / Server Overload", "enabled": True, "custom": False},
        {"pattern": "error running remote compact task", "name": "Remote Compact Task Error", "enabled": True, "custom": False},
        {"pattern": "stream disconnected", "name": "Stream Disconnected / Network Loss", "enabled": True, "custom": False},
        {"pattern": "connection lost", "name": "Connection Lost", "enabled": True, "custom": False},
        {"pattern": "rate limit", "name": "Rate Limit Exceeded", "enabled": True, "custom": False},
        {"pattern": "timeout", "name": "Request Timeout", "enabled": True, "custom": False},
        {"pattern": "an unexpected error occurred", "name": "Unexpected Server Error", "enabled": True, "custom": False},
        {"pattern": "serveroverloaded", "name": "Server Overloaded Code", "enabled": True, "custom": False}
    ],
    "excluded_projects": []
}

# -------------------------------------------------------------
# Словарь локализации (RU / EN)
# -------------------------------------------------------------
TRANSLATIONS = {
    "ru": {
        "menu_auto_resume_on": "🟢 Авто-возобновление: ВКЛЮЧЕНО",
        "menu_auto_resume_off": "⚪ Авто-возобновление: ВЫКЛЮЧЕНО",
        "menu_goals_submenu": "🎯 Задачи и цели Codex",
        "menu_no_goals": "(Нет недавних целей)",
        "menu_force_resume": "⚡ Возобновить цель сейчас",
        "menu_resumes_count": "📊 Возобновлено за сессию: {count}",
        "menu_settings": "⚙️ Настройки...",
        "menu_open_log": "📜 Открыть журнал (guardian.log)",
        "menu_open_folder": "📁 Открыть папку настроек (.codex)",
        "menu_autostart_windows": "🚀 Запускать при старте Windows",
        "menu_exit": "❌ Выход (закрыть сторож)",
        "tip_enabled": "Codex Auto-Resume: ВКЛЮЧЕНО",
        "tip_disabled": "Codex Auto-Resume: ВЫКЛЮЧЕНО (пауза)",
        "tip_goals": "Цели ({count}): {names}",
        "tip_resumes": "Возобновлений: {count}",
        "notif_app_title": "Codex Auto-Resume",
        "notif_started": "Сторож активен в системном трее.\nСостояние: {state}",
        "notif_state_on": "Авто-возобновление целей: ВКЛЮЧЕНО 🟢",
        "notif_state_off": "Авто-возобновление целей: ВЫКЛЮЧЕНО (пауза) ⚪",
        "notif_force_resume": "Запущено немедленное возобновление цели ⚡",
        "notif_autostart_on": "Автозагрузка при старте Windows включена.",
        "notif_autostart_off": "Автозагрузка при старте Windows отключена.",
        "dialog_title": "Настройки Codex Auto-Resume",
        "tab_general": "Общие и Запуск",
        "tab_errors": "Ошибки",
        "tab_projects": "Проекты",
        "tab_timers": "Тайминги и Лимиты",
        "grp_language": "Язык интерфейса",
        "lang_auto": "Автоматически (Язык системы)",
        "lang_ru": "Русский (Russian)",
        "lang_en": "English (Английский)",
        "grp_startup": "Параметры запуска",
        "chk_autostart_windows": "Запускать сторож при старте Windows",
        "chk_enable_on_codex_start": "Включать авто-возобновление при старте Кодекса",
        "grp_notifications": "Оповещения",
        "chk_notify_toggle": "Уведомление Windows при переключении (ярлык / трей)",
        "chk_notify_resume": "Уведомление Windows при возобновлении (может мешать играм)",
        "chk_sound_resume": "Звуковой сигнал при авто-возобновлении",
        "grp_error_patterns": "Отслеживаемые типы ошибок",
        "lbl_new_error": "Добавить новую ошибку (текст или ключевое слово):",
        "placeholder_new_error": "Например: rate limit reached или context length exceeded",
        "btn_add_error": "➕ Добавить",
        "btn_delete_error": "🗑️ Удалить выбранную",
        "btn_reset_errors": "🔄 Сбросить по умолчанию",
        "grp_projects": "Участвующие проекты",
        "lbl_projects_desc": "Сторож будет автоматически возобновлять цели только в отмеченных проектах:",
        "btn_select_all": "✅ Выбрать все",
        "btn_deselect_all": "❌ Снять все",
        "grp_timers": "Тайминги авто-возобновления",
        "lbl_retry_pause": "Пауза перед возобновлением после ошибки:",
        "lbl_cooldown": "Защитный кулдаун после успешного возобновления:",
        "lbl_poll_interval": "Интервал проверки состояния:",
        "lbl_max_retries": "Максимум попыток подряд:",
        "unit_seconds": "сек.",
        "unlimited": "Без ограничений",
        "btn_save": "💾 Сохранить",
        "btn_cancel": "Отмена",
        "btn_apply": "Применить",
        "msg_saved_title": "Успешно",
        "msg_saved_text": "Настройки успешно сохранены!"
    },
    "en": {
        "menu_auto_resume_on": "🟢 Auto-Resume: ENABLED",
        "menu_auto_resume_off": "⚪ Auto-Resume: DISABLED",
        "menu_goals_submenu": "🎯 Codex Goals & Tasks",
        "menu_no_goals": "(No recent goals)",
        "menu_force_resume": "⚡ Resume goal now",
        "menu_resumes_count": "📊 Resumed this session: {count}",
        "menu_settings": "⚙️ Settings...",
        "menu_open_log": "📜 Open log (guardian.log)",
        "menu_open_folder": "📁 Open settings folder (.codex)",
        "menu_autostart_windows": "🚀 Launch on Windows startup",
        "menu_exit": "❌ Exit (close watchdog)",
        "tip_enabled": "Codex Auto-Resume: ENABLED",
        "tip_disabled": "Codex Auto-Resume: DISABLED (Paused)",
        "tip_goals": "Goals ({count}): {names}",
        "tip_resumes": "Resumes: {count}",
        "notif_app_title": "Codex Auto-Resume",
        "notif_started": "Watchdog active in system tray.\nState: {state}",
        "notif_state_on": "Auto-Resume goals: ENABLED 🟢",
        "notif_state_off": "Auto-Resume goals: DISABLED (Paused) ⚪",
        "notif_force_resume": "Immediate goal resume triggered ⚡",
        "notif_autostart_on": "Windows startup launch enabled.",
        "notif_autostart_off": "Windows startup launch disabled.",
        "dialog_title": "Codex Auto-Resume Settings",
        "tab_general": "General and Startup",
        "tab_errors": "Errors",
        "tab_projects": "Projects",
        "tab_timers": "Timers and Limits",
        "grp_language": "Interface Language",
        "lang_auto": "Auto (System Default)",
        "lang_ru": "Russian (Русский)",
        "lang_en": "English",
        "grp_startup": "Startup Options",
        "chk_autostart_windows": "Launch watchdog on Windows startup",
        "chk_enable_on_codex_start": "Enable auto-resume when Codex starts",
        "grp_notifications": "Notifications",
        "chk_notify_toggle": "Windows notification on manual toggle (shortcut / tray)",
        "chk_notify_resume": "Windows notification on auto-resume (may disrupt games)",
        "chk_sound_resume": "Play sound chime on auto-resume",
        "grp_error_patterns": "Monitored Error Types",
        "lbl_new_error": "Add new error pattern (text or keyword):",
        "placeholder_new_error": "E.g.: rate limit reached or context length exceeded",
        "btn_add_error": "➕ Add",
        "btn_delete_error": "🗑️ Delete selected",
        "btn_reset_errors": "🔄 Reset to defaults",
        "grp_projects": "Participating Projects",
        "lbl_projects_desc": "Watchdog will automatically resume goals only in checked projects:",
        "btn_select_all": "✅ Select all",
        "btn_deselect_all": "❌ Deselect all",
        "grp_timers": "Auto-Resume Timings",
        "lbl_retry_pause": "Pause before retry after error:",
        "lbl_cooldown": "Safety cooldown after successful resume:",
        "lbl_poll_interval": "State polling interval:",
        "lbl_max_retries": "Max consecutive retries:",
        "unit_seconds": "sec.",
        "unlimited": "Unlimited",
        "btn_save": "💾 Save",
        "btn_cancel": "Cancel",
        "btn_apply": "Apply",
        "msg_saved_title": "Success",
        "msg_saved_text": "Settings saved successfully!"
    }
}

def detect_system_language():
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage() & 0x3FF
        if lang_id == 0x19:  # Russian
            return "ru"
    except Exception:
        pass
    return "en"

# -------------------------------------------------------------
# Менеджер настроек
# -------------------------------------------------------------
class SettingsManager:
    def __init__(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in data.items():
                    self.settings[k] = v
            except Exception:
                pass
        else:
            self.save()

    def save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_effective_language(self):
        lang = self.settings.get("language", "auto")
        if lang == "auto":
            return detect_system_language()
        return lang if lang in TRANSLATIONS else "ru"

    def tr(self, key, **kwargs):
        lang = self.get_effective_language()
        msg = TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)
        if kwargs:
            try:
                msg = msg.format(**kwargs)
            except Exception:
                pass
        return msg

    def get_error_patterns(self):
        patterns = self.settings.get("error_patterns", [])
        return [p["pattern"].lower() for p in patterns if p.get("enabled", True)]

    def is_project_enabled(self, project_path):
        if not project_path:
            return True
        excluded = self.settings.get("excluded_projects", [])
        norm_proj = os.path.normpath(project_path).lower()
        for exc in excluded:
            if os.path.normpath(exc).lower() == norm_proj:
                return False
        return True

settings_mgr = SettingsManager()

def get_all_codex_projects():
    projects = []
    seen = set()
    if not os.path.exists(SESSION_INDEX_FILE):
        return projects
    try:
        with open(SESSION_INDEX_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    cwd = obj.get("cwd")
                    if cwd and cwd not in seen:
                        seen.add(cwd)
                        name = os.path.basename(os.path.normpath(cwd)) or cwd
                        projects.append({"name": name, "path": cwd})
                except Exception:
                    pass
    except Exception:
        pass
    projects.sort(key=lambda x: x["name"].lower())
    return projects

# -------------------------------------------------------------
# Графический интерфейс окна настроек (Tkinter 100% Solid Dark)
# -------------------------------------------------------------
class SettingsWindow:
    def __init__(self, root=None):
        self.mgr = settings_mgr
        self.mgr.load()

        self.root = root or tk.Tk()
        self.root.title(self.mgr.tr("dialog_title"))
        self.root.geometry("720x640")
        self.root.minsize(660, 560)
        self.root.configure(bg="#181825")

        # Активация темной рамки Windows 11 DWM
        try:
            self.root.update_idletasks()
            hwnd = int(self.root.frame(), 16) if isinstance(self.root.frame(), str) else self.root.winfo_id()
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), 4)
        except Exception:
            pass

        # Иконка окна
        if os.path.exists(ICON_FILE):
            try:
                self.root.iconbitmap(ICON_FILE)
            except Exception:
                pass

        # Переменные настроек
        self.var_lang = tk.StringVar(value=self.mgr.settings.get("language", "auto"))
        self.var_autostart_win = tk.BooleanVar(value=bool(self.mgr.settings.get("autostart_windows", True)))
        self.var_codex_start = tk.BooleanVar(value=bool(self.mgr.settings.get("enable_on_codex_start", True)))
        self.var_notify_toggle = tk.BooleanVar(value=bool(self.mgr.settings.get("notify_on_toggle", True)))
        self.var_notify_resume = tk.BooleanVar(value=bool(self.mgr.settings.get("notify_on_resume", False)))
        self.var_sound_resume = tk.BooleanVar(value=bool(self.mgr.settings.get("sound_on_resume", False)))

        self.var_retry_pause = tk.IntVar(value=int(self.mgr.settings.get("retry_pause_seconds", 10)))
        self.var_cooldown = tk.IntVar(value=int(self.mgr.settings.get("post_resume_cooldown", 6)))
        self.var_poll = tk.StringVar(value=str(self.mgr.settings.get("poll_interval_seconds", 1.0)))
        self.var_max_retries = tk.IntVar(value=int(self.mgr.settings.get("max_retries_consecutive", 10)))

        self.error_vars = []   # [(var, item_dict)]
        self.project_vars = [] # [(var, proj_dict)]

        self.setup_styles()
        self.build_ui()
        self.apply_translations()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        bg_main = "#181825"
        bg_card = "#1e1e2e"
        bg_active = "#313244"
        fg_text = "#cdd6f4"
        fg_sub = "#a6adc8"
        accent_blue = "#89b4fa"

        self.style.configure(".", background=bg_main, foreground=fg_text, font=("Segoe UI", 10))
        self.style.configure("TNotebook", background=bg_main, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=bg_card, foreground=fg_sub, padding=[16, 8], font=("Segoe UI", 10, "bold"), borderwidth=1)
        self.style.map("TNotebook.Tab", background=[("selected", bg_active)], foreground=[("selected", accent_blue)])

        self.style.configure("TCombobox", fieldbackground="#181825", background=bg_card, foreground=fg_text, bordercolor="#45475a")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#181825")])

        self.style.configure("TSpinbox", fieldbackground="#181825", background=bg_card, foreground=fg_text, bordercolor="#45475a")

    def build_ui(self):
        # Контейнер вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(12, 6))

        # 1. Общие и Запуск
        self.tab_general = tk.Frame(self.notebook, bg="#1e1e2e", padx=18, pady=18)
        self.notebook.add(self.tab_general, text=" Общие и Запуск ")
        self.build_tab_general()

        # 2. Ошибки
        self.tab_errors = tk.Frame(self.notebook, bg="#1e1e2e", padx=18, pady=18)
        self.notebook.add(self.tab_errors, text=" Ошибки ")
        self.build_tab_errors()

        # 3. Проекты
        self.tab_projects = tk.Frame(self.notebook, bg="#1e1e2e", padx=18, pady=18)
        self.notebook.add(self.tab_projects, text=" Проекты ")
        self.build_tab_projects()

        # 4. Тайминги и Лимиты
        self.tab_timers = tk.Frame(self.notebook, bg="#1e1e2e", padx=18, pady=18)
        self.notebook.add(self.tab_timers, text=" Тайминги и Лимиты ")
        self.build_tab_timers()

        # Нижняя панель действий
        bottom_bar = tk.Frame(self.root, bg="#181825", padx=14, pady=10)
        bottom_bar.pack(fill="x", side="bottom")

        self.btn_cancel = tk.Button(
            bottom_bar, text="Отмена", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 10), relief="flat", padx=16, pady=6,
            command=self.root.destroy, cursor="hand2"
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_apply = tk.Button(
            bottom_bar, text="Применить", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 10), relief="flat", padx=16, pady=6,
            command=self.save_values, cursor="hand2"
        )
        self.btn_apply.pack(side="right", padx=(8, 0))

        self.btn_save = tk.Button(
            bottom_bar, text="💾 Сохранить", bg="#10b981", fg="#ffffff", activebackground="#059669",
            activeforeground="#ffffff", font=("Segoe UI", 10, "bold"), relief="flat", padx=20, pady=6,
            command=self.on_save_and_close, cursor="hand2"
        )
        self.btn_save.pack(side="right")

    def build_tab_general(self):
        self.lang_codes = ["auto", "ru", "en"]

        # 1. Группа Язык
        self.grp_lang = tk.LabelFrame(self.tab_general, text=" Язык интерфейса ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.grp_lang.pack(fill="x", pady=(0, 14))

        self.combo_lang = ttk.Combobox(self.grp_lang, state="readonly", font=("Segoe UI", 10))
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_language_selected)
        self.combo_lang.pack(anchor="w", fill="x", pady=4)

        # 2. Группа Запуск
        self.grp_startup = tk.LabelFrame(self.tab_general, text=" Параметры запуска ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.grp_startup.pack(fill="x", pady=(0, 14))

        self.chk_autostart_win = tk.Checkbutton(
            self.grp_startup, variable=self.var_autostart_win, bg="#1e1e2e", fg="#cdd6f4",
            activebackground="#1e1e2e", activeforeground="#89b4fa", selectcolor="#181825",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_autostart_win.pack(anchor="w", pady=4)

        self.chk_codex_start = tk.Checkbutton(
            self.grp_startup, variable=self.var_codex_start, bg="#1e1e2e", fg="#cdd6f4",
            activebackground="#1e1e2e", activeforeground="#89b4fa", selectcolor="#181825",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_codex_start.pack(anchor="w", pady=4)

        # 3. Группа Оповещения
        self.grp_notif = tk.LabelFrame(self.tab_general, text=" Оповещения ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.grp_notif.pack(fill="x")

        self.chk_notify_toggle = tk.Checkbutton(
            self.grp_notif, variable=self.var_notify_toggle, bg="#1e1e2e", fg="#cdd6f4",
            activebackground="#1e1e2e", activeforeground="#89b4fa", selectcolor="#181825",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_notify_toggle.pack(anchor="w", pady=4)

        self.chk_notify_resume = tk.Checkbutton(
            self.grp_notif, variable=self.var_notify_resume, bg="#1e1e2e", fg="#cdd6f4",
            activebackground="#1e1e2e", activeforeground="#89b4fa", selectcolor="#181825",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_notify_resume.pack(anchor="w", pady=4)

        self.chk_sound_resume = tk.Checkbutton(
            self.grp_notif, variable=self.var_sound_resume, bg="#1e1e2e", fg="#cdd6f4",
            activebackground="#1e1e2e", activeforeground="#89b4fa", selectcolor="#181825",
            font=("Segoe UI", 10), cursor="hand2"
        )
        self.chk_sound_resume.pack(anchor="w", pady=4)

    def build_tab_errors(self):
        self.grp_errors = tk.LabelFrame(self.tab_errors, text=" Отслеживаемые типы ошибок ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.grp_errors.pack(fill="both", expand=True)

        container = tk.Frame(self.grp_errors, bg="#181825", bd=1, relief="solid")
        container.pack(fill="both", expand=True, pady=(0, 10))

        self.canvas_errors = tk.Canvas(container, bg="#181825", highlightthickness=0)
        scrollbar_err = ttk.Scrollbar(container, orient="vertical", command=self.canvas_errors.yview)
        self.scroll_err_frame = tk.Frame(self.canvas_errors, bg="#181825")

        self.scroll_err_frame.bind("<Configure>", lambda e: self.canvas_errors.configure(scrollregion=self.canvas_errors.bbox("all")))
        self.canvas_errors_win = self.canvas_errors.create_window((0, 0), window=self.scroll_err_frame, anchor="nw")
        self.canvas_errors.bind("<Configure>", lambda e: self.canvas_errors.itemconfig(self.canvas_errors_win, width=e.width))
        self.canvas_errors.configure(yscrollcommand=scrollbar_err.set)

        self.canvas_errors.pack(side="left", fill="both", expand=True)
        scrollbar_err.pack(side="right", fill="y")

        self.populate_error_items()

        # Поле ввода новой ошибки
        self.lbl_new_error = tk.Label(self.grp_errors, text="Добавить новую ошибку:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 9))
        self.lbl_new_error.pack(anchor="w", pady=(4, 2))

        add_row = tk.Frame(self.grp_errors, bg="#1e1e2e")
        add_row.pack(fill="x", pady=(0, 8))

        self.entry_new_error = tk.Entry(add_row, bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4", font=("Segoe UI", 10), bd=1, relief="solid")
        self.entry_new_error.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        self.btn_add_error = tk.Button(
            add_row, text="➕ Добавить", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=4,
            command=self.on_add_error, cursor="hand2"
        )
        self.btn_add_error.pack(side="right")

        # Кнопки сброса и удаления
        ctrl_row = tk.Frame(self.grp_errors, bg="#1e1e2e")
        ctrl_row.pack(fill="x")

        self.btn_del_error = tk.Button(
            ctrl_row, text="🗑️ Удалить выбранную", bg="#313244", fg="#f38ba8", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 9), relief="flat", padx=10, pady=4,
            command=self.on_delete_error, cursor="hand2"
        )
        self.btn_del_error.pack(side="left")

        self.btn_reset_errors = tk.Button(
            ctrl_row, text="🔄 Сбросить по умолчанию", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 9), relief="flat", padx=10, pady=4,
            command=self.on_reset_errors, cursor="hand2"
        )
        self.btn_reset_errors.pack(side="right")

    def populate_error_items(self):
        for widget in self.scroll_err_frame.winfo_children():
            widget.destroy()
        self.error_vars.clear()

        patterns = self.mgr.settings.get("error_patterns", DEFAULT_SETTINGS["error_patterns"])
        for item in patterns:
            var = tk.BooleanVar(value=bool(item.get("enabled", True)))
            tag = "[Своя]" if item.get("custom", False) else "[Системная]"
            txt = f" {tag} {item.get('name', item['pattern'])} ({item['pattern']})"
            chk = tk.Checkbutton(
                self.scroll_err_frame, text=txt, variable=var, bg="#181825", fg="#cdd6f4",
                activebackground="#181825", activeforeground="#89b4fa", selectcolor="#11111b",
                font=("Segoe UI", 9), anchor="w", cursor="hand2"
            )
            chk.pack(fill="x", padx=6, pady=3)
            self.error_vars.append((var, item, chk))

    def on_add_error(self):
        text = self.entry_new_error.get().strip()
        if not text:
            return
        patterns = self.mgr.settings.setdefault("error_patterns", [])
        if any(p["pattern"].lower() == text.lower() for p in patterns):
            return
        patterns.append({
            "pattern": text,
            "name": text,
            "enabled": True,
            "custom": True
        })
        self.entry_new_error.delete(0, "end")
        self.populate_error_items()

    def on_delete_error(self):
        new_patterns = []
        for var, item, _ in self.error_vars:
            if item.get("custom") and not var.get():
                continue
            new_patterns.append(item)
        self.mgr.settings["error_patterns"] = new_patterns
        self.populate_error_items()

    def on_reset_errors(self):
        self.mgr.settings["error_patterns"] = [dict(p) for p in DEFAULT_SETTINGS["error_patterns"]]
        self.populate_error_items()

    def build_tab_projects(self):
        self.grp_projects = tk.LabelFrame(self.tab_projects, text=" Участвующие проекты ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=10)
        self.grp_projects.pack(fill="both", expand=True)

        self.lbl_projects_desc = tk.Label(
            self.grp_projects, text="Сторож будет автоматически возобновлять цели только в отмеченных проектах:",
            bg="#1e1e2e", fg="#a6adc8", font=("Segoe UI", 9), wraplength=640, justify="left"
        )
        self.lbl_projects_desc.pack(anchor="w", pady=(0, 8))

        container = tk.Frame(self.grp_projects, bg="#181825", bd=1, relief="solid")
        container.pack(fill="both", expand=True, pady=(0, 10))

        self.canvas_proj = tk.Canvas(container, bg="#181825", highlightthickness=0)
        scrollbar_p = ttk.Scrollbar(container, orient="vertical", command=self.canvas_proj.yview)
        self.scroll_proj_frame = tk.Frame(self.canvas_proj, bg="#181825")

        self.scroll_proj_frame.bind("<Configure>", lambda e: self.canvas_proj.configure(scrollregion=self.canvas_proj.bbox("all")))
        self.canvas_proj_win = self.canvas_proj.create_window((0, 0), window=self.scroll_proj_frame, anchor="nw")
        self.canvas_proj.bind("<Configure>", lambda e: self.canvas_proj.itemconfig(self.canvas_proj_win, width=e.width))
        self.canvas_proj.configure(yscrollcommand=scrollbar_p.set)

        self.canvas_proj.pack(side="left", fill="both", expand=True)
        scrollbar_p.pack(side="right", fill="y")

        self.populate_project_items()

        btn_row = tk.Frame(self.grp_projects, bg="#1e1e2e")
        btn_row.pack(fill="x")

        self.btn_select_all_proj = tk.Button(
            btn_row, text="✅ Выбрать все", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 9), relief="flat", padx=12, pady=4,
            command=self.on_select_all_projects, cursor="hand2"
        )
        self.btn_select_all_proj.pack(side="left", padx=(0, 8))

        self.btn_deselect_all_proj = tk.Button(
            btn_row, text="❌ Снять все", bg="#313244", fg="#cdd6f4", activebackground="#45475a",
            activeforeground="#ffffff", font=("Segoe UI", 9), relief="flat", padx=12, pady=4,
            command=self.on_deselect_all_projects, cursor="hand2"
        )
        self.btn_deselect_all_proj.pack(side="left")

    def populate_project_items(self):
        for widget in self.scroll_proj_frame.winfo_children():
            widget.destroy()
        self.project_vars.clear()

        projects = get_all_codex_projects()
        excluded = set(os.path.normpath(p).lower() for p in self.mgr.settings.get("excluded_projects", []))

        for proj in projects:
            p_norm = os.path.normpath(proj["path"]).lower()
            is_checked = (p_norm not in excluded)
            var = tk.BooleanVar(value=is_checked)
            txt = f" 📁 {proj['name']}  —  {proj['path']}"
            chk = tk.Checkbutton(
                self.scroll_proj_frame, text=txt, variable=var, bg="#181825", fg="#cdd6f4",
                activebackground="#181825", activeforeground="#89b4fa", selectcolor="#11111b",
                font=("Segoe UI", 9), anchor="w", cursor="hand2"
            )
            chk.pack(fill="x", padx=6, pady=3)
            self.project_vars.append((var, proj))

    def on_select_all_projects(self):
        for var, _ in self.project_vars:
            var.set(True)

    def on_deselect_all_projects(self):
        for var, _ in self.project_vars:
            var.set(False)

    def build_tab_timers(self):
        self.grp_timers = tk.LabelFrame(self.tab_timers, text=" Тайминги авто-возобновления ", bg="#1e1e2e", fg="#89b4fa", font=("Segoe UI", 10, "bold"), padx=14, pady=12)
        self.grp_timers.pack(fill="both", expand=True)

        # 1. Пауза перед возобновлением
        self.lbl_retry_pause = tk.Label(self.grp_timers, text="Пауза перед возобновлением после ошибки:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_retry_pause.pack(anchor="w", pady=(4, 2))

        row1 = tk.Frame(self.grp_timers, bg="#1e1e2e")
        row1.pack(fill="x", pady=(0, 14))

        self.scale_retry = tk.Scale(
            row1, from_=2, to=60, orient="horizontal", variable=self.var_retry_pause,
            bg="#1e1e2e", fg="#10b981", activebackground="#10b981", highlightthickness=0,
            troughcolor="#313244", font=("Segoe UI", 9), showvalue=0, command=self.update_timer_labels
        )
        self.scale_retry.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.val_retry_lbl = tk.Label(row1, text="10 сек.", bg="#1e1e2e", fg="#10b981", font=("Segoe UI", 10, "bold"), width=8, anchor="e")
        self.val_retry_lbl.pack(side="right")

        # 2. Кулдаун
        self.lbl_cooldown = tk.Label(self.grp_timers, text="Защитный кулдаун после успешного возобновления:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_cooldown.pack(anchor="w", pady=(4, 2))

        row2 = tk.Frame(self.grp_timers, bg="#1e1e2e")
        row2.pack(fill="x", pady=(0, 14))

        self.scale_cooldown = tk.Scale(
            row2, from_=2, to=30, orient="horizontal", variable=self.var_cooldown,
            bg="#1e1e2e", fg="#10b981", activebackground="#10b981", highlightthickness=0,
            troughcolor="#313244", font=("Segoe UI", 9), showvalue=0, command=self.update_timer_labels
        )
        self.scale_cooldown.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.val_cooldown_lbl = tk.Label(row2, text="6 сек.", bg="#1e1e2e", fg="#10b981", font=("Segoe UI", 10, "bold"), width=8, anchor="e")
        self.val_cooldown_lbl.pack(side="right")

        # 3. Интервал опроса
        self.lbl_poll = tk.Label(self.grp_timers, text="Интервал проверки состояния:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_poll.pack(anchor="w", pady=(4, 2))

        self.combo_poll = ttk.Combobox(self.grp_timers, state="readonly", font=("Segoe UI", 10))
        self.combo_poll["values"] = ["0.5 сек. (Быстрый)", "1.0 сек. (Стандартный)", "2.0 сек. (Энергосберегающий)"]
        cur_poll = float(self.mgr.settings.get("poll_interval_seconds", 1.0))
        if cur_poll <= 0.6:
            self.combo_poll.current(0)
        elif cur_poll >= 1.8:
            self.combo_poll.current(2)
        else:
            self.combo_poll.current(1)
        self.combo_poll.pack(fill="x", pady=(0, 14))

        # 4. Максимум попыток подряд
        self.lbl_max_retries = tk.Label(self.grp_timers, text="Максимум попыток подряд:", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
        self.lbl_max_retries.pack(anchor="w", pady=(4, 2))

        self.spin_retries = ttk.Spinbox(self.grp_timers, from_=0, to=50, textvariable=self.var_max_retries, font=("Segoe UI", 10))
        self.spin_retries.pack(fill="x")

        self.update_timer_labels()

    def update_timer_labels(self, _=None):
        u = self.mgr.tr("unit_seconds")
        self.val_retry_lbl.config(text=f"{self.var_retry_pause.get()} {u}")
        self.val_cooldown_lbl.config(text=f"{self.var_cooldown.get()} {u}")

    def on_language_selected(self, event=None):
        idx = self.combo_lang.current()
        if 0 <= idx < len(self.lang_codes):
            code = self.lang_codes[idx]
            self.var_lang.set(code)
            self.mgr.settings["language"] = code
            self.apply_translations()

    def apply_translations(self):
        tr = self.mgr.tr
        self.root.title(tr("dialog_title"))

        lang_labels = [tr("lang_auto"), tr("lang_ru"), tr("lang_en")]
        self.combo_lang["values"] = lang_labels
        cur_code = self.var_lang.get()
        if cur_code in self.lang_codes:
            self.combo_lang.current(self.lang_codes.index(cur_code))

        self.notebook.tab(0, text=f"  {tr('tab_general')}  ")
        self.notebook.tab(1, text=f"  {tr('tab_errors')}  ")
        self.notebook.tab(2, text=f"  {tr('tab_projects')}  ")
        self.notebook.tab(3, text=f"  {tr('tab_timers')}  ")

        self.grp_lang.config(text=f" {tr('grp_language')} ")
        self.grp_startup.config(text=f" {tr('grp_startup')} ")
        self.chk_autostart_win.config(text=f" {tr('chk_autostart_windows')}")
        self.chk_codex_start.config(text=f" {tr('chk_enable_on_codex_start')}")

        self.grp_notif.config(text=f" {tr('grp_notifications')} ")
        self.chk_notify_toggle.config(text=f" {tr('chk_notify_toggle')}")
        self.chk_notify_resume.config(text=f" {tr('chk_notify_resume')}")
        self.chk_sound_resume.config(text=f" {tr('chk_sound_resume')}")

        self.grp_errors.config(text=f" {tr('grp_error_patterns')} ")
        self.lbl_new_error.config(text=tr("lbl_new_error"))
        self.btn_add_error.config(text=tr("btn_add_error"))
        self.btn_del_error.config(text=tr("btn_delete_error"))
        self.btn_reset_errors.config(text=tr("btn_reset_errors"))

        self.grp_projects.config(text=f" {tr('grp_projects')} ")
        self.lbl_projects_desc.config(text=tr("lbl_projects_desc"))
        self.btn_select_all_proj.config(text=tr("btn_select_all"))
        self.btn_deselect_all_proj.config(text=tr("btn_deselect_all"))

        self.grp_timers.config(text=f" {tr('grp_timers')} ")
        self.lbl_retry_pause.config(text=tr("lbl_retry_pause"))
        self.lbl_cooldown.config(text=tr("lbl_cooldown"))
        self.lbl_poll.config(text=tr("lbl_poll_interval"))
        self.lbl_max_retries.config(text=tr("lbl_max_retries"))

        self.btn_save.config(text=tr("btn_save"))
        self.btn_cancel.config(text=tr("btn_cancel"))
        self.btn_apply.config(text=tr("btn_apply"))

        self.update_timer_labels()

    def save_values(self):
        s = self.mgr.settings
        s["language"] = self.var_lang.get()
        s["autostart_windows"] = self.var_autostart_win.get()
        s["enable_on_codex_start"] = self.var_codex_start.get()
        s["notify_on_toggle"] = self.var_notify_toggle.get()
        s["notify_on_resume"] = self.var_notify_resume.get()
        s["sound_on_resume"] = self.var_sound_resume.get()

        s["retry_pause_seconds"] = float(self.var_retry_pause.get())
        s["post_resume_cooldown"] = float(self.var_cooldown.get())

        poll_idx = self.combo_poll.current()
        poll_map = {0: 0.5, 1: 1.0, 2: 2.0}
        s["poll_interval_seconds"] = poll_map.get(poll_idx, 1.0)

        s["max_retries_consecutive"] = int(self.var_max_retries.get())

        for var, item, _ in self.error_vars:
            item["enabled"] = var.get()

        excluded = []
        for var, proj in self.project_vars:
            if not var.get():
                excluded.append(proj["path"])
        s["excluded_projects"] = excluded

        self.mgr.save()

        # Автозагрузка Windows
        try:
            enable = s["autostart_windows"]
            pyw = sys.executable.replace("python.exe", "pythonw.exe")
            app_py = os.path.join(APP_DIR, "codex_tray_app.py")
            if enable:
                vbs = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """{pyw}"" """{app_py}""", 0, False\n'
                os.makedirs(os.path.dirname(AUTOSTART_VBS), exist_ok=True)
                with open(AUTOSTART_VBS, "w", encoding="utf-8") as f:
                    f.write(vbs)
            else:
                if os.path.exists(AUTOSTART_VBS):
                    os.remove(AUTOSTART_VBS)
        except Exception:
            pass

    def on_save_and_close(self):
        self.save_values()
        self.root.destroy()

# Dummy class for compatibility if imported as SettingsDialog
class SettingsDialog:
    def __init__(self, parent=None):
        pass

def open_settings_dialog():
    # Защита от открытия нескольких окон одновременно
    hwnd = win32_find_settings_window()
    if hwnd:
        user32 = ctypes.windll.user32
        user32.SetForegroundWindow(hwnd)
        user32.ShowWindow(hwnd, 9) # SW_RESTORE
        return

    root = tk.Tk()
    app = SettingsWindow(root)
    root.mainloop()

def win32_find_settings_window():
    import win32gui
    found = []
    def cb(h, _):
        txt = win32gui.GetWindowText(h)
        if any(txt.startswith(t) for t in ("Настройки Codex Auto-Resume", "Codex Auto-Resume Settings")):
            found.append(h)
        return True
    try:
        win32gui.EnumWindows(cb, None)
    except Exception:
        pass
    return found[0] if found else None

if __name__ == "__main__":
    open_settings_dialog()
