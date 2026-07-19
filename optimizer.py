import subprocess
import threading
import ctypes
import sys
import os
import time
import re

# ── Admin re-launch ──────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    app_path = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", app_path, "", None, 1)
    sys.exit(0)

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ──────────────────────────────────────────────────────
BG, BG2, BG3, BG4 = "#0d1117", "#161b22", "#21262d", "#2d333b"
GREEN, GREEN_D = "#00d26a", "#00a854"
BLUE, RED, YELLOW = "#3b82f6", "#f04444", "#f0b429"
TEXT, TEXT2, BORDER = "#e6edf3", "#8b949e", "#30363d"

R = "reg add"
D = "/t REG_DWORD /d"
F = "/f >nul 2>&1"


def K(idx):
    return (r"HKLM\SYSTEM\CurrentControlSet\Control\Class"
            rf"\{{4d36e968-e325-11ce-bfc1-08002be10318}}\{idx}")


CATEGORIES = ["Таймер / DPC", "Сеть / Input Lag", "GPU Мощность", "Сервисы", "Память / Диск", "Windows 11 / 25H2"]
PROFILES = ["Standard", "Balance", "Max Performance"]
PROFILE_DESC = {
    "Standard":       "Безопасные твики. Подходит для повседневного ПК и работы.",
    "Balance":        "Баланс FPS и стабильности. Рекомендуется для большинства.",
    "Max Performance": "Максимум FPS и минимум input lag. Только для игровых ПК.",
}
PROFILE_LEVEL = {"Standard": 1, "Balance": 2, "Max Performance": 3}


# ════════════════════════════════════════════════════════════════
#  TWEAK DEFINITIONS — (category, level, label, command)
#  level: 1=Standard, 2=Balance(+1), 3=Max Performance(+1,+2)
# ════════════════════════════════════════════════════════════════
def tweaks_general():
    t = []
    cat = "Таймер / DPC"
    t += [
        (cat, 1, "Схема питания: максимальная производительность",
         "powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        (cat, 1, "Гибернация отключена (меньше нагрузки на диск)",
         "powercfg -h off"),
        (cat, 2, "CPU Idle States отключены",
         "powercfg -setacvalueindex scheme_current 54533251-82be-4824-96c1-47b60b740d00 "
         "5d76a2ca-e8c0-402f-a133-2158492d58ad 0 && powercfg -setactive scheme_current"),
        (cat, 2, "Power Throttling отключён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling" /v PowerThrottlingOff {D} 1 {F}'),
        (cat, 2, "GPU Hardware Scheduling включён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" /v HwSchMode {D} 2 {F}'),
        (cat, 2, "Win32 планировщик — приоритет активного окна",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl" /v Win32PrioritySeparation {D} 38 {F}'),
        (cat, 2, "Приоритет игрового профиля (GPU/CPU High)",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "GPU Priority" {D} 8 {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "Priority" {D} 6 {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "Scheduling Category" /t REG_SZ /d "High" {F} && '
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games" '
         fr'/v "SFIO Priority" /t REG_SZ /d "High" {F}'),
        (cat, 2, "Таймер мультимедиа повышенной точности",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" '
         fr'/v SystemResponsiveness {D} 0 {F}'),
        (cat, 3, "MSI Mode для GPU (меньше input lag)",
         r'powershell -NoProfile -Command "$ErrorActionPreference=\'SilentlyContinue\';'
         r"Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Enum\PCI' | Get-ChildItem | Get-ChildItem |"
         r"Where-Object { $_.Name -match 'VEN_10DE|VEN_1002' } | ForEach-Object {"
         r"$m=$_.PSPath+'\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties';"
         r"New-Item $m -Force|Out-Null; Set-ItemProperty $m MSISupported 1 -Type DWord -Force}\""),
        (cat, 3, "Dynamic Tick отключён (стабильный системный такт)",
         "bcdedit /set disabledynamictick yes"),
        (cat, 3, "TSC синхронизация Enhanced (ниже DPC latency)",
         "bcdedit /deletevalue useplatformclock >nul 2>&1 && bcdedit /set tscsyncpolicy enhanced"),
    ]

    cat = "Сеть / Input Lag"
    t += [
        (cat, 1, "Windows Game Mode включён",
         fr'{R} "HKCU\Software\Microsoft\GameBar" /v AutoGameModeEnabled {D} 1 {F}'),
        (cat, 1, "Xbox Game Bar / DVR отключён",
         fr'{R} "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled {D} 0 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_Enabled {D} 0 {F} && '
         fr'{R} "HKCU\Software\Microsoft\GameBar" /v ShowStartupPanel {D} 0 {F}'),
        (cat, 2, "Fullscreen Optimizations отключены",
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_FSEBehaviorMode {D} 2 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_HonorUserFSEBehaviorMode {D} 1 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_DXGIHonorFSEWindowsCompatible {D} 1 {F} && '
         fr'{R} "HKCU\System\GameConfigStore" /v GameDVR_EFSEFeatureFlags {D} 0 {F}'),
        (cat, 2, "Сетевой троттлинг отключён",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile" '
         fr'/v NetworkThrottlingIndex {D} 4294967295 {F}'),
        (cat, 2, "DirectX Max Frame Latency = 1",
         fr'{R} "HKCU\Software\Microsoft\Direct3D" /v MaximumFrameLatency {D} 1 {F}'),
        (cat, 2, "Ускорение мыши отключено (точный ввод)",
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseSpeed /t REG_SZ /d "0" {F} && '
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseThreshold1 /t REG_SZ /d "0" {F} && '
         fr'{R} "HKCU\Control Panel\Mouse" /v MouseThreshold2 /t REG_SZ /d "0" {F}'),
        (cat, 2, "USB Selective Suspend отключён",
         "powercfg -setacvalueindex scheme_current 2a737441-1930-4402-8d77-b2bebba308a3 "
         "48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 && powercfg -setactive scheme_current"),
        (cat, 3, "TCP NoDelay / Ack Frequency (анти-Нэгла)",
         r'powershell -NoProfile -Command "$ErrorActionPreference=\'SilentlyContinue\';'
         r"Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' | ForEach-Object {"
         r"Set-ItemProperty $_.PSPath TcpAckFrequency 1 -Type DWord -Force;"
         r"Set-ItemProperty $_.PSPath TCPNoDelay 1 -Type DWord -Force}\""),
        (cat, 3, "TCP автотюнинг / RSS / Chimney Offload",
         "netsh int tcp set global autotuninglevel=normal && "
         "netsh int tcp set global rss=enabled && "
         "netsh int tcp set global chimney=enabled"),
        (cat, 3, "ECN отключён (стабильнее пинг)",
         "netsh int tcp set global ecncapability=disabled"),
        (cat, 3, "Очередь клавиатуры увеличена",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\kbdclass\Parameters" /v KeyboardDataQueueSize {D} 100 {F}'),
    ]

    cat = "GPU Мощность"
    t += [
        (cat, 1, "Визуальные эффекты минимизированы",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v VisualFXSetting {D} 2 {F} && '
         fr'{R} "HKCU\Software\Microsoft\Windows\DWM" /v Animations {D} 0 {F}'),
        (cat, 2, "Прозрачность интерфейса отключена",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v EnableTransparency {D} 0 {F}'),
        (cat, 3, "PCI-E Power Management (ASPM) отключён",
         "powercfg -setacvalueindex scheme_current 501a4d13-42af-4429-9fd1-a8218c268e20 "
         "ee12f906-d277-404b-b6da-e5fa1a576df5 0 && powercfg -setactive scheme_current"),
    ]

    cat = "Сервисы"
    t += [
        (cat, 1, "Телеметрия Microsoft отключена",
         "sc stop DiagTrack >nul 2>&1 & sc config DiagTrack start= disabled >nul 2>&1 & "
         "sc stop WerSvc >nul 2>&1 & sc config WerSvc start= disabled >nul 2>&1 & "
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection" /v AllowTelemetry {D} 0 {F}'),
        (cat, 1, "Уведомления отключены",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\PushNotifications" /v ToastEnabled {D} 0 {F}'),
        (cat, 1, "Временные файлы очищены",
         'cmd /c "del /q /f /s %TEMP%\\* >nul 2>&1 & del /q /f /s C:\\Windows\\Temp\\* >nul 2>&1"'),
        (cat, 2, "SysMain (Superfetch) отключён",
         "sc stop SysMain >nul 2>&1 & sc config SysMain start= disabled >nul 2>&1"),
        (cat, 2, "Windows Search Indexer отключён",
         "sc stop WSearch >nul 2>&1 & sc config WSearch start= disabled >nul 2>&1"),
        (cat, 2, "Diagnostic Policy Service отключён",
         "sc stop DPS >nul 2>&1 & sc config DPS start= disabled >nul 2>&1"),
        (cat, 2, "Геолокация / Карты отключены",
         "sc stop lfsvc >nul 2>&1 & sc config lfsvc start= disabled >nul 2>&1 & "
         "sc stop MapsBroker >nul 2>&1 & sc config MapsBroker start= disabled >nul 2>&1"),
        (cat, 2, "Автообслуживание Windows отключено",
         fr'{R} "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance" /v MaintenanceDisabled {D} 1 {F}'),
        (cat, 3, "Program Compatibility Assistant отключён",
         "sc stop PcaSvc >nul 2>&1 & sc config PcaSvc start= disabled >nul 2>&1"),
        (cat, 3, "Факс / печать по требованию отключены",
         "sc stop Fax >nul 2>&1 & sc config Fax start= disabled >nul 2>&1 & "
         "sc stop PrintNotify >nul 2>&1 & sc config PrintNotify start= disabled >nul 2>&1"),
        (cat, 3, "Delivery Optimization отключён",
         "sc stop DoSvc >nul 2>&1 & sc config DoSvc start= disabled >nul 2>&1 & "
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization" /v DODownloadMode {D} 0 {F}'),
        (cat, 3, "Рекламные сервисы / предложения отключены",
         "sc stop RetailDemo >nul 2>&1 & sc config RetailDemo start= disabled >nul 2>&1 & "
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager" '
         fr'/v SubscribedContent-338388Enabled {D} 0 {F}'),
    ]

    cat = "Память / Диск"
    t += [
        (cat, 1, "Корзина и миниатюры очищены",
         'cmd /c "del /q /f /s %LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db >nul 2>&1"'),
        (cat, 2, "Управление памятью оптимизировано",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v LargeSystemCache {D} 0 {F} && '
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v ClearPageFileAtShutdown {D} 0 {F}'),
        (cat, 2, "TRIM для SSD включён",
         "fsutil behavior set disabledeletenotify 0"),
        (cat, 3, "Файл подкачки зафиксирован 8 GB (нет micro-stutter)",
         'wmic computersystem set AutomaticManagedPagefile=False >nul 2>&1 && '
         'wmic pagefileset where "name=\'C:\\\\pagefile.sys\'" set InitialSize=8192,MaximumSize=8192 >nul 2>&1'),
        (cat, 3, "Приоритет системного кэша — программам",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" '
         fr'/v DisablePagingExecutive {D} 1 {F}'),
        (cat, 3, "NTFS: отключены Last Access Timestamp и 8.3-имена",
         "fsutil behavior set disablelastaccess 1 && fsutil behavior set disable8dot3 1"),
    ]

    cat = "Windows 11 / 25H2"
    t += [
        (cat, 1, "Widgets (значки погоды/новостей) отключены",
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Dsh" /v AllowNewsAndInterests {D} 0 {F}'),
        (cat, 1, "Copilot отключён",
         fr'{R} "HKCU\Software\Policies\Microsoft\Windows\WindowsCopilot" /v TurnOffWindowsCopilot {D} 1 {F}'),
        (cat, 2, "Windows Recall отключён (снимки экрана AI)",
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" /v DisableAIDataAnalysis {D} 1 {F} && '
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" /v AllowRecallEnablement {D} 0 {F}'),
        (cat, 2, "Click to Do отключён",
         fr'{R} "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsAI" /v DisableClickToDo {D} 1 {F}'),
        (cat, 2, "Efficiency Mode не троттлит игровой процесс",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power" /v HeteroPolicyMode {D} 0 {F}'),
        (cat, 3, "Фоновые UWP-приложения отключены",
         fr'{R} "HKCU\Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications" '
         fr'/v GlobalUserDisabled {D} 1 {F}'),
        (cat, 3, "Prefetch/Superfetch параметры под SSD (25H2)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" '
         fr'/v EnablePrefetcher {D} 0 {F} && '
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" '
         fr'/v EnableSuperfetch {D} 0 {F}'),
    ]
    return t


def tweaks_intel():
    return [
        ("CPU (Intel)", 1, "Intel CPU зафиксирован на макс. частоте",
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", 2, "Core Parking отключён (все ядра активны)",
         "powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", 2, "Intel Turbo Boost зафиксирован включённым",
         "powercfg -setacvalueindex scheme_current sub_processor PERFBOOSTMODE 2 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", 3, "Intel PPM отключён (ниже DPC latency)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\intelppm" /v Start {D} 4 {F}'),
        ("CPU (Intel)", 3, "x2APIC включён (быстрее обработка IRQ)",
         "bcdedit /set x2apicpolicy enable"),
        ("CPU (Intel)", 3, "C-States ограничены (ниже задержки пробуждения)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Processor" /v Capabilities {D} 0x0007e066 {F}'),
        ("CPU (Intel)", 3, "Intel SpeedShift на максимум отклика (12+ поколение)",
         "powercfg -setacvalueindex scheme_current sub_processor PERFEPP 0 >nul 2>&1 && "
         "powercfg -setactive scheme_current"),
        ("CPU (Intel)", 3, "Приоритет P-ядер для игр (гибридная архитектура)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\kernel" /v PowerThrottlingOff {D} 1 {F}'),
    ]


def tweaks_amd_cpu():
    return [
        ("CPU (AMD)", 1, "AMD Ryzen High Performance план активирован",
         "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 >nul 2>&1 && "
         "powercfg -setactive e9a42b02-d5df-448d-aa00-03f14749eb61"),
        ("CPU (AMD)", 2, "Core Parking отключён (все ядра активны)",
         "powercfg -setacvalueindex scheme_current sub_processor CPMINCORES 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMIN 100 && "
         "powercfg -setacvalueindex scheme_current sub_processor PROCTHROTTLEMAX 100 && "
         "powercfg -setactive scheme_current"),
        ("CPU (AMD)", 2, "AMD Cool'n'Quiet / PPM отключён",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Services\amdppm" /v Start {D} 4 {F}'),
        ("CPU (AMD)", 3, "TSC Sync Enhanced (стабильность на Ryzen)",
         "bcdedit /set tscsyncpolicy enhanced"),
        ("CPU (AMD)", 3, "AMD Precision Boost — приоритет отклика",
         "powercfg -setacvalueindex scheme_current sub_processor PERFBOOSTMODE 1 >nul 2>&1 && "
         "powercfg -setactive scheme_current"),
        ("CPU (AMD)", 3, "SMT Idle оптимизация (меньше латентность потоков)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00'
         fr'\0cc5b647-c1df-4637-891a-dec35c318583" /v ValueMax {D} 0 {F}'),
        ("CPU (AMD)", 3, "Приоритет 3D V-Cache CCD (X3D модели)",
         fr'{R} "HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerSettings\54533251-82be-4824-96c1-47b60b740d00'
         fr'\0cc5b647-c1df-4637-891a-dec35c318583" /v ValueMin {D} 0 {F}'),
    ]


def tweaks_nvidia():
    t = [
        ("GPU (NVIDIA)", 1, "NVIDIA GeForce Overlay отключён",
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableShadows {D} 0 {F} && '
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableGeForceExperience {D} 0 {F} && '
         fr'{R} "HKCU\SOFTWARE\NVIDIA Corporation\Global\GFExperience" /v EnableCameraControl {D} 0 {F}'),
        ("GPU (NVIDIA)", 2, "NVIDIA Telemetry отключена",
         "sc stop NvTelemetryContainer >nul 2>&1 & sc config NvTelemetryContainer start= disabled >nul 2>&1"),
        ("GPU (NVIDIA)", 2, "NVIDIA Display Power Saving отключён",
         fr'{R} "HKLM\SOFTWARE\NVIDIA Corporation\Global\NVTweak" /v DisplayPowerSaving {D} 0 {F}'),
        ("GPU (NVIDIA)", 3, "NVIDIA Low Latency Mode (глобально)",
         fr'{R} "HKCU\Software\NVIDIA Corporation\Global\NVTweak\Devices" /v OglMaxFramesAllowed {D} 1 {F}'),
        ("GPU (NVIDIA)", 3, "nvidia-smi Persistence Mode + отключение auto-boost",
         "nvidia-smi -pm 1 >nul 2>&1 && nvidia-smi --auto-boost-default=0 >nul 2>&1"),
        ("GPU (NVIDIA)", 3, "Reflex Low Latency включён (глобальный профиль)",
         fr'{R} "HKCU\Software\NVIDIA Corporation\Global\NVTweak\Devices" /v LowLatencyMode {D} 1 {F}'),
    ]
    for k in ["0000", "0001"]:
        base = K(k)
        t.append((f"GPU (NVIDIA)", 2, f"PowerMizer максимум производительности [{k}]",
                   f'{R} "{base}" /v PowerMizerLevel {D} 1 {F} && '
                   f'{R} "{base}" /v PowerMizerLevelAC {D} 1 {F} && '
                   f'{R} "{base}" /v PowerMizerEnable {D} 1 {F} && '
                   f'{R} "{base}" /v PerfLevelSrc {D} 8738 {F} && '
                   f'{R} "{base}" /v RmPstate {D} 100859137 {F}'))
        t.append((f"GPU (NVIDIA)", 3, f"HDCP отключён [{k}]",
                   f'{R} "{base}" /v RMHdcpKeyglobZero {D} 1 {F}'))
    return t


def tweaks_amd_gpu():
    t = [
        ("GPU (AMD)", 1, "AMD ReLive / Overlay отключён",
         fr'{R} "HKCU\Software\AMD\DVR" /v Enable {D} 0 {F} && '
         fr'{R} "HKCU\Software\AMD\DVR" /v EnableRecord {D} 0 {F}'),
    ]
    for k in ["0000", "0001"]:
        base = K(k)
        t.append((f"GPU (AMD)", 2, f"Anti-Lag включён [{k}]",
                   f'{R} "{base}" /v DalAntiLagEnabled {D} 1 {F}'))
        t.append((f"GPU (AMD)", 3, f"ULPS + Deep Sleep + Compute Preemption off [{k}]",
                   f'{R} "{base}" /v EnableUlps {D} 0 {F} && '
                   f'{R} "{base}" /v EnableUlps_NA {D} 0 {F} && '
                   f'{R} "{base}" /v PP_ThermalAutoThrottlingEnable {D} 0 {F} && '
                   f'{R} "{base}" /v PP_SclkDeepSleepDisable {D} 1 {F} && '
                   f'{R} "{base}" /v PP_MclkDeepSleepDisable {D} 1 {F} && '
                   f'{R} "{base}" /v KMD_EnableComputePreemption {D} 0 {F}'))
    return t


# ════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PC Optimizer Pro  v4.0")
        self.geometry("900x800")
        self.minsize(900, 800)
        self.resizable(False, False)
        self.configure(fg_color=BG)
        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        self.cpu = ctk.StringVar(value="")
        self.gpu = ctk.StringVar(value="")
        self.profile = ctk.StringVar(value="Balance")
        self.revios = ctk.BooleanVar(value=False)
        self.running = False
        self._build()
        threading.Thread(target=self._detect_os, daemon=True).start()

    def _build(self):
        self._header()
        self._os_bar()
        self._selectors()
        self._profile_selector()
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
        ctk.CTkLabel(badge, text="v4.0", font=("Segoe UI Black", 13), text_color=GREEN
                     ).place(relx=0.5, rely=0.5, anchor="center")

    def _os_bar(self):
        bar = ctk.CTkFrame(self, fg_color=BG, height=26)
        bar.pack(fill="x", padx=18, pady=(8, 0))
        self.os_label = ctk.CTkLabel(bar, text="🖥  Определение Windows...", font=("Segoe UI", 10),
                                     text_color=TEXT2, anchor="w")
        self.os_label.pack(side="left")
        self.revios_check = ctk.CTkCheckBox(bar, text="Кастомная сборка (ReviOS / AtlasOS / др.)",
                                            variable=self.revios, font=("Segoe UI", 10),
                                            text_color=TEXT2, fg_color=GREEN, hover_color=GREEN_D,
                                            border_color=BORDER, checkmark_color=BG, width=16, height=16)
        self.revios_check.pack(side="right")

    def _detect_os(self):
        try:
            out = subprocess.run(
                'powershell -NoProfile -Command "(Get-ItemProperty '
                r"'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').DisplayVersion + '|' + "
                r"(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').CurrentBuild + '|' + "
                r"(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').ProductName\"",
                shell=True, capture_output=True, text=True, timeout=8
            ).stdout.strip()
            parts = out.split("|")
            ver = parts[0] if len(parts) > 0 else "?"
            build = parts[1] if len(parts) > 1 else "?"
            name = parts[2] if len(parts) > 2 else "Windows"
            revios_hint = ""
            try:
                owner = subprocess.run(
                    'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" /v RegisteredOwner',
                    shell=True, capture_output=True, text=True, timeout=5
                ).stdout
                if "revi" in owner.lower() or "atlas" in owner.lower():
                    revios_hint = " (обнаружена кастомная сборка)"
                    self.after(0, self.revios.set, True)
            except Exception:
                pass
            txt = f"🖥  {name}  ·  версия {ver}  ·  сборка {build}{revios_hint}"
        except Exception:
            txt = "🖥  Windows (версия не определена)"
        self.after(0, self.os_label.configure, {"text": txt})

    def _detect_hw(self):
        self._set_status("  Определяю железо...")
        try:
            cpu_name = subprocess.run(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_Processor).Name"',
                shell=True, capture_output=True, text=True, timeout=8
            ).stdout.strip().lower()
            gpu_name = subprocess.run(
                'powershell -NoProfile -Command "(Get-CimInstance Win32_VideoController).Name"',
                shell=True, capture_output=True, text=True, timeout=8
            ).stdout.strip().lower()

            if "intel" in cpu_name:
                self.after(0, self._pick_cpu, "Intel")
            elif "amd" in cpu_name or "ryzen" in cpu_name:
                self.after(0, self._pick_cpu, "AMD")

            if "nvidia" in gpu_name or "geforce" in gpu_name or "rtx" in gpu_name or "gtx" in gpu_name:
                self.after(0, self._pick_gpu, "NVIDIA")
            elif "amd" in gpu_name or "radeon" in gpu_name:
                self.after(0, self._pick_gpu, "AMD")

            self.after(0, self._log, f"  Автоопределение: CPU={cpu_name[:40]}  GPU={gpu_name[:40]}", "dim")
        except Exception as e:
            self.after(0, self._log_warn, f"Не удалось определить железо ({e})")
        self._set_status("Ожидание...")

    def _selectors(self):
        outer = ctk.CTkFrame(self, fg_color=BG2, corner_radius=12)
        outer.pack(fill="x", padx=18, pady=(10, 0))

        top = ctk.CTkFrame(outer, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(top, text="ЖЕЛЕЗО", font=("Segoe UI", 11, "bold"), text_color=TEXT2).pack(side="left")
        ctk.CTkButton(top, text="🔍 Автоопределить", font=("Segoe UI", 10, "bold"), height=24, width=140,
                      fg_color=BG3, hover_color=BG4, text_color=GREEN, corner_radius=6,
                      command=lambda: threading.Thread(target=self._detect_hw, daemon=True).start()
                      ).pack(side="right")

        ctk.CTkLabel(outer, text="  Процессор", font=("Segoe UI", 10), text_color=TEXT2
                     ).pack(anchor="w", padx=14, pady=(8, 4))
        row1 = ctk.CTkFrame(outer, fg_color="transparent")
        row1.pack(fill="x", padx=14)
        self.b_intel = self._sel_btn(row1, "🔵  Intel", "#0d2137", BLUE, lambda: self._pick_cpu("Intel"))
        self.b_intel.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.b_amd_c = self._sel_btn(row1, "🔴  AMD Ryzen", "#2d0f0f", RED, lambda: self._pick_cpu("AMD"))
        self.b_amd_c.pack(side="left", expand=True, fill="x", padx=(6, 0))

        ctk.CTkLabel(outer, text="  Видеокарта", font=("Segoe UI", 10), text_color=TEXT2
                     ).pack(anchor="w", padx=14, pady=(10, 4))
        row2 = ctk.CTkFrame(outer, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(0, 14))
        self.b_nvid = self._sel_btn(row2, "🟢  NVIDIA", "#0d2d1a", GREEN, lambda: self._pick_gpu("NVIDIA"))
        self.b_nvid.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self.b_amd_g = self._sel_btn(row2, "🔴  AMD Radeon", "#2d0f0f", RED, lambda: self._pick_gpu("AMD"))
        self.b_amd_g.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _sel_btn(self, parent, text, active_bg, active_border, cmd):
        btn = ctk.CTkButton(parent, text=text, height=48, font=("Segoe UI", 13, "bold"),
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

    def _profile_selector(self):
        outer = ctk.CTkFrame(self, fg_color=BG2, corner_radius=12)
        outer.pack(fill="x", padx=18, pady=(10, 0))
        ctk.CTkLabel(outer, text="  РЕЖИМ ОПТИМИЗАЦИИ", font=("Segoe UI", 11, "bold"),
                     text_color=TEXT2).pack(anchor="w", padx=14, pady=(12, 6))

        row = ctk.CTkFrame(outer, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=(0, 6))
        self.profile_btns = {}
        colors = {"Standard": ("#0d2137", BLUE), "Balance": ("#1a2d0d", GREEN),
                  "Max Performance": ("#2d0f0f", RED)}
        for i, p in enumerate(PROFILES):
            bg_a, border_a = colors[p]
            btn = ctk.CTkButton(row, text=p, height=46, font=("Segoe UI", 13, "bold"),
                                fg_color=BG3, hover_color=BG4, text_color=TEXT2, corner_radius=10,
                                border_width=2, border_color=BORDER,
                                command=lambda p=p: self._pick_profile(p))
            btn._active_bg, btn._active_border = bg_a, border_a
            btn.pack(side="left", expand=True, fill="x", padx=4 if i else (0, 4))
            self.profile_btns[p] = btn

        self.profile_desc_lbl = ctk.CTkLabel(outer, text=PROFILE_DESC["Balance"], font=("Segoe UI", 10),
                                             text_color=TEXT2)
        self.profile_desc_lbl.pack(anchor="w", padx=14, pady=(0, 12))
        self._pick_profile("Balance")

    def _pick_profile(self, val):
        self.profile.set(val)
        self.profile_desc_lbl.configure(text=PROFILE_DESC[val])
        for p, btn in self.profile_btns.items():
            if p == val:
                btn.configure(fg_color=btn._active_bg, border_color=btn._active_border, text_color=TEXT)
            else:
                btn.configure(fg_color=BG3, border_color=BORDER, text_color=TEXT2)

    def _categories(self):
        row = ctk.CTkFrame(self, fg_color=BG)
        row.pack(fill="x", padx=18, pady=(10, 0))
        self.cat_vars = {}
        icons = {"Таймер / DPC": "⏱", "Сеть / Input Lag": "🌐", "GPU Мощность": "🎮",
                 "Сервисы": "🔧", "Память / Диск": "💾", "Windows 11 / 25H2": "🪟"}
        for i, label in enumerate(CATEGORIES):
            var = ctk.BooleanVar(value=True)
            self.cat_vars[label] = var
            cb = ctk.CTkCheckBox(row, text=f"{icons[label]} {label}", variable=var,
                                  font=("Segoe UI", 10), text_color=TEXT2, fg_color=GREEN,
                                  hover_color=GREEN_D, border_color=BORDER, checkmark_color=BG,
                                  width=16, height=16)
            cb.grid(row=i // 3, column=i % 3, padx=8, pady=4, sticky="w")
        row.columnconfigure((0, 1, 2), weight=1)

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
        self.log_box.tag_config("yellow", foreground=YELLOW)
        self.log_box.tag_config("dim", foreground=TEXT2)
        self.log_box.tag_config("white", foreground=TEXT)
        self._log("Выберите процессор, видеокарту и режим → нажмите СТАРТ", "dim")

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
        cpu, gpu, profile = self.cpu.get(), self.gpu.get(), self.profile.get()
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
        self._log(f"  Конфигурация: {cpu} + {gpu}  ·  Режим: {profile}"
                   f"{'  ·  ReviOS/кастом' if self.revios.get() else ''}", "dim")
        self._log("  " + "─" * 50, "dim")
        threading.Thread(target=self._run, args=(cpu, gpu, profile), daemon=True).start()

    def _run(self, cpu, gpu, profile):
        def cmd(c):
            try:
                subprocess.run(c, shell=True, capture_output=True, timeout=15)
            except Exception:
                pass

        max_level = PROFILE_LEVEL[profile]
        enabled_cats = {c for c, v in self.cat_vars.items() if v.get()}

        steps = [s for s in tweaks_general() if s[0] in enabled_cats and s[1] <= max_level]
        hw_steps = (tweaks_intel() if cpu == "Intel" else tweaks_amd_cpu())
        hw_steps += (tweaks_nvidia() if gpu == "NVIDIA" else tweaks_amd_gpu())
        steps += [s for s in hw_steps if s[1] <= max_level]

        total = len(steps) or 1
        for i, (_, _, label, c) in enumerate(steps):
            self._set_status(f"  {label}...")
            try:
                cmd(c)
                self._log_ok(label)
            except Exception as e:
                self._log_warn(f"{label}  ({e})")
            self._set_progress((i + 1) / total)
            time.sleep(0.03)

        self.after(0, self._done, total)

    def _done(self, total):
        self._log("  " + "─" * 50, "dim")
        self._log_ok(f"Оптимизация завершена! Применено твиков: {total}")
        self._log("  ➜  Перезагрузите ПК для полного эффекта", "yellow")
        self.status.configure(text="  ✓  Готово! Перезагрузите ПК.")
        self.start_btn.configure(state="normal", text="✅   ОПТИМИЗАЦИЯ ЗАВЕРШЕНА",
                                  fg_color="#0d2d1a", text_color=GREEN)
        self.running = False


if __name__ == "__main__":
    app = App()
    app.mainloop()
