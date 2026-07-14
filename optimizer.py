import subprocess
import threading
import ctypes
import sys
import os
import time

# ── Admin re-launch ──────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    app_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", app_path, "", None, 1)
    sys.exit(0)

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Colors ───────────────────────────────────────────────────────
BG, BG2, BG3, BG4 = "#0d1117", "#161b22", "#21262d", "#2d333b"
GREEN, GREEN_D = "#00d26a", "#00a854"
BLUE, RED = "#3b82f6", "#f04444"
TEXT, TEXT2, BORDER = "#e6edf3", "#8b949e", "#30363d"

R = "reg add"
D = "/t REG_DWORD /d"
F = "/f >nul 2>&1"


def K(idx):
    return (r"HKLM\SYSTEM\CurrentControlSet\Control\Class"
            rf"\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{idx}")


# ════════════════════════════════════════════════════════════════
#  TWEAK DEFINITIONS — (category, label, command)
# ════════════════════════════════════════════════════════════════
def tweaks_general():
    cat = "Таймер / DPC"
    t = [
        (cat, "Схема питания: максимальная производительность",
         "powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        (cat, "CPU Idle States отключены",
         "powercfg -setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 "
         "5d76a2ca-e8c0-402f-a133-2158492d58ad 0 && powercfg -setactive scheme_current"),
        (cat, "Power Throttling отключён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff {D} 1 {F}'),
        (cat, "Гибернация отключена (меньше нагрузки на диск)",
         "powercfg -h off"),
        (cat, "Dynamic Tick отключён (стабильный системный такт)",
         "bcdedit /set disabledynamictick yes"),
        (cat, "Платформенные часы синхронизированы (TSC)",
         "bcdedit /deletevalue useplatformclock && bcdedit /set tscsyncpolicy enhanced"),
        (cat, "HPET отключён (ниже latency на большинстве систем)",
         "bcdedit /deletevalue useplatformclock >nul 2>&1 && bcdedit /set disabledynamictick yes"),
        (cat, "GPU Hardware Scheduling включён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode {D} 2 {F}'),
        (cat, "Win32 планировщик — приоритет активного окна",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v Win32PrioritySeparation {D} 38 {F}'),
        (cat, "Приоритет игрового профиля (GPU/CPU High)",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "GPU Priority" {D} 8 {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "Priority" {D} 6 {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "Scheduling Category" /t REG_SZ /d "High" {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "SFIO Priority" /t REG_SZ /d "High" {F}'),
        (cat, "MSI Mode для GPU (меньше input lag)",
         r'powershell -NoProfile -Command "$ErrorActionPreference=\'SilentlyContinue\';'
         r"Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Enum\PCI' | Get-ChildItem | Get-ChildItem |"
         r"Where-Object { $_.Name -match 'VEN_10DE|VEN_1002' } | ForEach-Object {"
         r"$m=$_.PSPath+'\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties';"
         r"New-Item $m -Force|Out-Null; Set-ItemProperty $m MSISupported 1 -Type DWord -Force}\""),
        (cat, "Таймер мультимедиа повышенной точности",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" '
         fr'/v SystemResponsiveness {D} 0 {F}'),
    ]

    cat = "Сеть / Input Lag"
    t += [
        (cat, "Сетевой троттлинг отключён",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" '
         fr'/v NetworkThrottlingIndex {D} 4294967295 {F}'),
        (cat, "TCP NoDelay / Ack Frequency (анти-Нэгла)",
         r'powershell -NoProfile -Command "$ErrorActionPreference=\'SilentlyContinue\';'
         r"Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' | ForEach-Object {"
         r"Set-ItemProperty $_.PSPath TcpAckFrequency 1 -Type DWord -Force;"
         r"Set-ItemProperty $_.PSPath TCPNoDelay 1 -Type DWord -Force}\""),
        (cat, "TCP автотюнинг оптимизирован",
         "netsh int tcp set global autotuninglevel=normal"),
        (cat, "TCP Chimney Offload включён (ниже CPU нагрузка сети)",
         "netsh int tcp set global chimney=enabled"),
        (cat, "RSS (Receive Side Scaling) включён",
         "netsh int tcp set global rss=enabled"),
        (cat, "ECN отключён (стабильнее пинг в некоторых играх)",
         "netsh int tcp set global ecncapability=disabled"),
        (cat, "DirectX Max Frame Latency = 1",
         fr'{R} "HKCU\Software\Microsoft\Direct3D" /v MaximumFrameLatency {D} 1 {F}'),
        (cat, "Ускорение мыши отключено (точный ввод)",
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "0" {F} && '
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" {F} && '
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" {F}'),
        (cat, "Частота опроса клавиатуры повышена",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\kbdclass\Parameters" '
         fr'/v KeyboardDataQueueSize {D} 100 {F}'),
        (cat, "USB Selective Suspend отключён",
         "powercfg -setacvalueindex scheme_current 2a737441-1930-4402-8d77-b2bebba308a3 "
         "48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 && powercfg -setactive scheme_current"),
        (cat, "Fullscreen Optimizations отключены",
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_FSEBehaviorMode {D} 2 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_HonorUserFSEBehaviorMode {D} 1 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_DXGIHonorFSEWindowsCompatible {D} 1 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_EFSEFeatureFlags {D} 0 {F}'),
        (cat, "Xbox Game Bar / DVR отключён",
         fr'{R} "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled {D} 0 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_Enabled {D} 0 {F} && '
         fr'{R} "HKCU\Software\Microsoft\GameBar" /v ShowStartupPanel {D} 0 {F}'),
        (cat, "Windows Game Mode включён",
         fr'{R} "HKCU\Software\Microsoft\GameBar" /v AutoGameModeEnabled {D} 1 {F}'),
    ]

    cat = "GPU Мощность"
    t += [
        (cat, "PCI-E Power Management (ASPM) отключён",
         "powercfg -setacvalueindex scheme_current 501a4d13-42af-4429-9fd1-a8218c268e20 "
         "ee12f906-d277-404b-b6da-e5fa1a576df5 0 && powercfg -setactive scheme_current"),
        (cat, "Визуальные эффекты минимизированы",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting {D} 2 {F} && '
         fr'{R} "HKCU\Software\Microsoft\Windows\DWM" /v Animations {D} 0 {F}'),
        (cat, "Прозрачность интерфейса отключена",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency {D} 0 {F}'),
    ]

    cat = "Сервисы"
    t += [
        (cat, "Телеметрия Microsoft отключена",
         "sc stop DiagTrack >nul 2>&1 & sc config DiagTrack start= disabled >nul 2>&1 & "
         "sc stop WerSvc >nul 2>&1 & sc config WerSvc start= disabled >nul 2>&1 & "
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry {D} 0 {F}'),
        (cat, "SysMain (Superfetch) отключён",
         "sc stop SysMain >nul 2>&1 & sc config SysMain start= disabled >nul 2>&1"),
        (cat, "Windows Search Indexer отключён",
         "sc stop WSearch >nul 2>&1 & sc config WSearch start= disabled >nul 2>&1"),
        (cat, "Diagnostic Policy Service отключён",
         "sc stop DPS >nul 2>&1 & sc config DPS start= disabled >nul 2>&1"),
        (cat, "Геолокация / Карты отключены",
         "sc stop lfsvc >nul 2>&1 & sc config lfsvc start= disabled >nul 2>&1 & "
         "sc stop MapsBroker >nul 2>&1 & sc config MapsBroker start= disabled >nul 2>&1"),
        (cat, "Program Compatibility Assistant отключён",
         "sc stop PcaSvc >nul 2>&1 & sc config PcaSvc start= disabled >nul 2>&1"),
        (cat, "Факс и печать по требованию отключены",
         "sc stop Fax >nul 2>&1 & sc config Fax start= disabled >nul 2>&1 & "
         "sc stop PrintNotify >nul 2>&1 & sc config PrintNotify start= disabled >nul 2>&1"),
        (cat, "Delivery Optimization отключён",
         "sc stop DoSvc >nul 2>&1 & sc config DoSvc start= disabled >nul 2>&1 & "
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v DODownloadMode {D} 0 {F}'),
        (cat, "Retail Demo / рекламные сервисы отключены",
         "sc stop RetailDemo >nul 2>&1 & sc config RetailDemo start= disabled >nul 2>&1 & "
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" '
         fr'/v SubscribedContent-338388Enabled {D} 0 {F}'),
        (cat, "Автообслуживание Windows отключено",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance" /v MaintenanceDisabled {D} 1 {F}'),
        (cat, "Уведомления отключены",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled {D} 0 {F}'),
    ]

    cat = "Память / Диск"
    t += [
        (cat, "Управление памятью оптимизировано",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v LargeSystemCache {D} 0 {F} && '
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v ClearPageFileAtShutdown {D} 0 {F}'),
        (cat, "Файл подкачки зафиксирован 8 GB (нет micro-stutter)",
         'wmic computersystem set AutomaticManagedPagefile=False >nul 2>&1 && '
         'wmic pagefileset where "name=\'C:\\\\pagefile.sys\'" set InitialSize=8192,MaximumSize=8192 >nul 2>&1'),
        (cat, "Приоритет системного кэша — программам",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v DisablePagingExecutive {D} 1 {F}'),
        (cat, "NTFS: отключены Last Access Timestamp",
         "fsutil behavior set disablelastaccess 1"),
        (cat, "NTFS: отключена 8.3 имена файлов",
         "fsutil behavior set disable8dot3 1"),
        (cat, "TRIM для SSD включён",
         "fsutil behavior set disabledeletenotify 0"),
        (cat, "Временные файлы очищены",
         'cmd /c "del /q /f /s %TEMP%\\* >nul 2>&1 & del /q /f /s C:\\Windows\\Temp\\* >nul 2>&1"'),
        (cat, "Корзина и миниатюры очищены",
         'cmd /c "del /q /f /s %LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db >nul 2>&1"'),
    ]
    return t


def tweaks_intel():
    return [
        ("CPU (Intel)", "Intel PPM отключён (ниже DPC latency)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\intelppm" /v Start {D} 4 {F}'),
        ("CPU (Intel)", "Intel CPU зафиксирован на макс. частоте",
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", "Core Parking отключён (все ядра активны)",
         "powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", "x2APIC включён (быстрее обработка IRQ)",
         "bcdedit /set x2apicpolicy enable"),
        ("CPU (Intel)", "Intel Turbo Boost зафиксирован включённым",
         "powercfg -setacvalueindex scheme_current sub_processor PERFBOOSTMODE 2 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", "Intel SpeedShift на максимум отклика",
         "powercfg -setacvalueindex scheme_current sub_processor PERFEPP 0 >nul 2>&1 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", "C-States ограничены (ниже задержки пробуждения)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Processor" /v Capabilities {D} 0x0007e066 {F}'),
    ]


def tweaks_amd_cpu():
    return [
        ("CPU (AMD)", "AMD Ryzen High Performance план активирован",
         "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul 2>&1 && "
         "powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61"),
        ("CPU (AMD)", "AMD Cool'n'Quiet / PPM отключён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\amdppm" /v Start {D} 4 {F}'),
        ("CPU (AMD)", "Core Parking отключён (все ядра активны)",
         "powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (AMD)", "TSC Sync Enhanced (стабильность на Ryzen)",
         "bcdedit /set tscsyncpolicy enhanced"),
        ("CPU (AMD)", "AMD Precision Boost Overdrive — приоритет отклика",
         "powercfg -setacvalueindex scheme_current sub_processor PERFBOOSTMODE 1 >nul 2>&1 && "
         "powercfg -setactive scheme_current"),
        ("CPU (AMD)", "SMT Idle оптимизация (меньше латентность потоков)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00'
         fr'\0cc5b647-c1df-4637-891a-dec35c318583" /v ValueMax {D} 0 {F}'),
    ]


def tweaks_nvidia():
    t = [
        ("GPU (NVIDIA)", "NVIDIA Telemetry отключена",
         "sc stop NvTelemetryContainer >nul 2>&1 & sc config NvTelemetryContainer start= disabled >nul 2>&1"),
        ("GPU (NVIDIA)", "NVIDIA GeForce Overlay отключён",
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableShadows {D} 0 {F} && '
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableGeForceExperience {D} 0 {F} && '
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableCameraControl {D} 0 {F}'),
        ("GPU (NVIDIA)", "NVIDIA Display Power Saving отключён",
         fr'{R} "HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak" /v DisplayPowerSaving {D} 0 {F}'),
        ("GPU (NVIDIA)", "NVIDIA Low Latency Mode (глобально)",
         fr'{R} "HKCU\Software\NVIDIA Corporation\Global\NVTweak\Devices" /v OglMaxFramesAllowed {D} 1 {F}'),
        ("GPU (NVIDIA)", "nvidia-smi Persistence Mode + отключение авто-boost",
         "nvidia-smi -pm 1 >nul 2>&1 && nvidia-smi --auto-boost-default=0 >nul 2>&1"),
    ]
    for k in ["0000", "0001"]:
        base = K(k)
        t.append((f"GPU (NVIDIA)", f"PowerMizer + HDCP оптимизация [{k}]",
                   f'{R} "{base}" /v PowerMizerLevel {D} 1 {F} && '
                   f'{R} "{base}" /v PowerMizerLevelAC {D} 1 {F} && '
                   f'{R} "{base}" /v PowerMizerEnable {D} 1 {F} && '
                   f'{R} "{base}" /v PerfLevelSrc {D} 8738 {F} && '
                   f'{R} "{base}" /v RMHdcpKeyglobZero {D} 1 {F} && '
                   f'{R} "{base}" /v RmPstate {D} 100859137 {F}'))
    return t


def tweaks_amd_gpu():
    t = [
        ("GPU (AMD)", "AMD ReLive / Overlay отключён",
         fr'{R} "HKCU\Software\AMD\DVR" /v Enable {D} 0 {F} && '
         fr'{R} "HKCU\Software\AMD\DVR" /v EnableRecord {D} 0 {F}'),
    ]
    for k in ["0000", "0001"]:
        base = K(k)
        t.append((f"GPU (AMD)", f"ULPS + Anti-Lag + Deep Sleep off [{k}]",
                   f'{R} "{base}" /v EnableUlps {D} 0 {F} && '
                   f'{R} "{base}" /v EnableUlps_NA {D} 0 {F} && '
                   f'{R} "{base}" /v PP_ThermalAutoThrottlingEnable {D} 0 {F} && '
                   f'{R} "{base}" /v PP_SclkDeepSleepDisable {D} 1 {F} && '
                   f'{R} "{base}" /v PP_MclkDeepSleepDisable {D} 1 {F} && '
                   f'{R} "{base}" /v DalAntiLagEnabled {D} 1 {F} && '
                   f'{R} "{base}" /v KMD_EnableComputePreemption {D} 0 {F}'))
    return t


CATEGORIES = ["Таймер / DPC", "Сеть / Input Lag", "GPU Мощность", "Сервисы", "Память / Диск"]


# ════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PC Optimizer Pro  v3.0")
        self.geometry("860x720")
        self.minsize(860, 720)
        self.resizable(False, False)
        self.configure(fg_color=BG)
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        self.cpu = ctk.StringVar(value="")
        self.gpu = ctk.StringVar(value="")
        self.running = False
        self._build()

    def _build(self):
        self._header()
        self._selectors()
        self._categories()
        self._log_area()
        self._footer()

    def _header(self):
        hdr = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, height=72)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="⚡  PC OPTIMIZER PRO", font=("Segoe UI Black", 22, "bold"),
                     text_color=GREEN).place(x=22, y=14)
        ctk.CTkLabel(hdr, text="MAX FPS  ·  LOW INPUT LAG  ·  NO STUTTER", font=("Segoe UI", 11),
                     text_color=TEXT2).place(x=26, y=46)
        badge = ctk.CTkFrame(hdr, fg_color=BG3, corner_radius=8, width=90, height=38)
        badge.place(relx=1.0, x=-20, y=17, anchor="ne")
        ctk.CTkLabel(badge, text="v3.0", font=("Segoe UI Black", 13), text_color=GREEN
                     ).place(relx=0.5, rely=0.5, anchor="center")

    def _selectors(self):
        outer = ctk.CTkFrame(self, fg_color=BG2, corner_radius=12)
        outer.pack(fill="x", padx=18, pady=(14, 0))
        ctk.CTkLabel(outer, text="  ПРОЦЕССОР", font=("Segoe UI", 11, "bold"),
                     text_color=TEXT2).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))
        self.b_intel = self._sel_btn(outer, "🔵  Intel", "#0d2137", BLUE, lambda: self._pick_cpu("Intel"))
        self.b_intel.grid(row=1, column=0, padx=(14, 6), pady=(0, 14))
        self.b_amd_c = self._sel_btn(outer, "🔴  AMD Ryzen", "#2d0f0f", RED, lambda: self._pick_cpu("AMD"))
        self.b_amd_c.grid(row=1, column=1, padx=(0, 14), pady=(0, 14))
        ctk.CTkFrame(outer, fg_color=BORDER, height=1).grid(row=2, column=0, columnspan=2, sticky="ew", padx=14)
        ctk.CTkLabel(outer, text="  ВИДЕОКАРТА", font=("Segoe UI", 11, "bold"),
                     text_color=TEXT2).grid(row=3, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 6))
        self.b_nvid = self._sel_btn(outer, "🟢  NVIDIA", "#0d2d1a", GREEN, lambda: self._pick_gpu("NVIDIA"))
        self.b_nvid.grid(row=4, column=0, padx=(14, 6), pady=(0, 14))
        self.b_amd_g = self._sel_btn(outer, "🔴  AMD Radeon", "#2d0f0f", RED, lambda: self._pick_gpu("AMD"))
        self.b_amd_g.grid(row=4, column=1, padx=(0, 14), pady=(0, 14))
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)

    def _sel_btn(self, parent, text, active_bg, active_border, cmd):
        btn = ctk.CTkButton(parent, text=text, height=52, font=("Segoe UI", 13, "bold"),
                             fg_color=BG3, hover_color=BG4, text_color=TEXT2, corner_radius=10,
                             border_width=2, border_color=BORDER, command=cmd)
        btn._active_bg = active_bg
        btn._active_border = active_border
        return btn

    def _pick_cpu(self, val):
        self.cpu.set(val)
        for btn, v in [(self.b_intel, "Intel"), (self.b_amd_c, "AMD")]:
            if v == val:
                btn.configure(fg_color=btn._active_bg, border_color=btn._active_border, text_color=TEXT)
            else:
                btn.configure(fg_color=BG3, border_color=BORDER, text_color=TEXT2)

    def _pick_gpu(self, val):
        self.gpu.set(val)
        for btn, v in [(self.b_nvid, "NVIDIA"), (self.b_amd_g, "AMD")]:
            if v == val:
                btn.configure(fg_color=btn._active_bg, border_color=btn._active_border, text_color=TEXT)
            else:
                btn.configure(fg_color=BG3, border_color=BORDER, text_color=TEXT2)

    def _categories(self):
        row = ctk.CTkFrame(self, fg_color=BG)
        row.pack(fill="x", padx=18, pady=(10, 0))
        self.cat_vars = {}
        icons = {"Таймер / DPC": "⏱", "Сеть / Input Lag": "🌐", "GPU Мощность": "🎮",
                 "Сервисы": "🔧", "Память / Диск": "💾"}
        for i, label in enumerate(CATEGORIES):
            var = ctk.BooleanVar(value=True)
            self.cat_vars[label] = var
            cb = ctk.CTkCheckBox(row, text=f"{icons[label]}  {label}", variable=var,
                                  font=("Segoe UI", 11), text_color=TEXT2, fg_color=GREEN,
                                  hover_color=GREEN_D, border_color=BORDER, checkmark_color=BG,
                                  width=20, height=20)
            cb.grid(row=0, column=i, padx=10, pady=6, sticky="w")
        row.columnconfigure(tuple(range(len(CATEGORIES))), weight=1)

    def _log_area(self):
        wrap = ctk.CTkFrame(self, fg_color=BG2, corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=18, pady=(10, 0))
        ctk.CTkLabel(wrap, text="  ЛОГ ОПТИМИЗАЦИИ", font=("Segoe UI", 11, "bold"),
                     text_color=TEXT2).pack(anchor="w", padx=14, pady=(10, 4))
        self.log_box = ctk.CTkTextbox(wrap, font=("Consolas", 11), fg_color=BG, text_color=TEXT,
                                       border_width=1, border_color=BORDER, corner_radius=8,
                                       activate_scrollbars=True)
        self.log_box.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.log_box.tag_config("green", foreground=GREEN)
        self.log_box.tag_config("yellow", foreground="#f0b429")
        self.log_box.tag_config("dim", foreground=TEXT2)
        self.log_box.tag_config("white", foreground=TEXT)
        self._log("Выберите процессор и видеокарту → нажмите СТАРТ", "dim")

    def _footer(self):
        ft = ctk.CTkFrame(self, fg_color=BG2, corner_radius=0, height=100)
        ft.pack(fill="x")
        ft.pack_propagate(False)
        self.progress = ctk.CTkProgressBar(ft, height=6, corner_radius=3, fg_color=BG3, progress_color=GREEN)
        self.progress.place(x=18, y=16, relwidth=1.0, width=-36)
        self.progress.set(0)
        self.status = ctk.CTkLabel(ft, text="Ожидание...", font=("Segoe UI", 11), text_color=TEXT2)
        self.status.place(x=20, y=30)
        self.start_btn = ctk.CTkButton(ft, text="⚡   НАЧАТЬ ОПТИМИЗАЦИЮ", font=("Segoe UI Black", 14, "bold"),
                                        height=44, corner_radius=10, fg_color=GREEN, hover_color=GREEN_D,
                                        text_color="#0d1117", command=self._start)
        self.start_btn.place(x=18, y=46, relwidth=1.0, width=-36)

    def _log(self, msg, tag="white"):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _log_ok(self, msg):
        self.after(0, self._log, f"  ✓  {msg}", "green")

    def _log_warn(self, msg):
        self.after(0, self._log, f"  ⚠  {msg}", "yellow")

    def _set_status(self, txt):
        self.after(0, self.status.configure, {"text": txt})

    def _set_progress(self, v):
        self.after(0, self.progress.set, v)

    def _start(self):
        cpu, gpu = self.cpu.get(), self.gpu.get()
        if not cpu:
            self._log("  ⚠  Выберите процессор!", "yellow"); return
        if not gpu:
            self._log("  ⚠  Выберите видеокарту!", "yellow"); return
        if self.running:
            return
        self.running = True
        self.start_btn.configure(state="disabled", text="⏳   ОПТИМИЗАЦИЯ...", fg_color=BG3, text_color=TEXT2)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        self._log(f"  Конфигурация: {cpu} + {gpu}", "dim")
        self._log("  " + "─" * 50, "dim")
        threading.Thread(target=self._run, args=(cpu, gpu), daemon=True).start()

    def _run(self, cpu, gpu):
        def cmd(c):
            try:
                subprocess.run(c, shell=True, capture_output=True, timeout=15)
            except Exception:
                pass

        enabled_cats = {c for c, v in self.cat_vars.items() if v.get()}

        steps = [s for s in tweaks_general() if s[0] in enabled_cats]
        steps += tweaks_intel() if cpu == "Intel" else tweaks_amd_cpu()
        steps += tweaks_nvidia() if gpu == "NVIDIA" else tweaks_amd_gpu()

        total = len(steps) or 1
        for i, (_, label, c) in enumerate(steps):
            self._set_status(f"  {label}...")
            try:
                cmd(c)
                self._log_ok(label)
            except Exception as e:
                self._log_warn(f"{label}  ({e})")
            self._set_progress((i + 1) / total)
            time.sleep(0.04)

        self.after(0, self._done)

    def _done(self):
        self._log("  " + "─" * 50, "dim")
        self._log_ok("Оптимизация завершена!")
        self._log("  ➜  Перезагрузите ПК для полного эффекта", "yellow")
        self.status.configure(text="  ✓  Готово! Перезагрузите ПК.")
        self.start_btn.configure(state="normal", text="✅   ОПТИМИЗАЦИЯ ЗАВЕРШЕНА",
                                  fg_color="#0d2d1a", text_color=GREEN)
        self.running = False


if __name__ == "__main__":
    app = App()
    app.mainloop()
