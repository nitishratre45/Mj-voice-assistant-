from pathlib import Path
import os
import subprocess
import webbrowser
from pathlib import Path


class AppLauncher:
    """
    MJ Universal App Launcher
    """

    APP_ALIASES = {

        "chrome": [
            "chrome",
            "google chrome",
            "browser",
        ],

        "vscode": [
            "vscode",
            "visual studio code",
            "code",
        ],

        "calculator": [
            "calculator",
            "calc",
            "calculate",
        ],

        "notepad": [
            "notepad",
            "note pad",
            "notes",
        ],

        "paint": [
            "paint",
            "mspaint",
        ],

        "explorer": [
            "file explorer",
            "files",
            "explorer",
        ],

        "cmd": [
            "cmd",
            "command prompt",
        ],

        "task manager": [
            "task manager",
            "taskmanager",
        ],
        "settings": [
            "settings",
            "windows settings",
        ],

        "whatsapp": [
            "whatsapp",
            "whatsap",
        ],

        "telegram": [
            "telegram",
        ],

        "discord": [
            "discord",
        ],

        "whatsapp": [
            "whatsapp",
        ],
    }


    def normalize(self, text):

        return (
            str(text or "")
            .lower()
            .strip()
        )


    def find_app(self, name):

        name = self.normalize(name)

        for app, aliases in self.APP_ALIASES.items():

            if name in aliases:
                return app

            for a in aliases:
                if a in name:
                    return app

        return name




    # =====================================================
    # MJ WINDOW CONTROL
    # =====================================================

    def control_window(self, command):

        command = command.lower().strip()


        close_apps = {

            "chrome": "chrome.exe",
            "edge": "msedge.exe",
            "vscode": "Code.exe",
            "excel": "EXCEL.EXE",
            "word": "WINWORD.EXE",
            "powerpoint": "POWERPNT.EXE",
            "telegram": "Telegram.exe",
            "discord": "Discord.exe",
            "spotify": "Spotify.exe",
            "whatsapp": "WhatsApp.exe",

        }


        if "close" in command or "band" in command:

            for name, exe in close_apps.items():

                if name in command:

                    subprocess.Popen(
                        f"taskkill /f /im {exe}",
                        shell=True
                    )

                    return (
                        f"{name} band kar diya.",
                        "hi",
                        True,
                    )


        if "minimize" in command or "chhota" in command:

            subprocess.Popen(
                'powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"',
                shell=True
            )

            return (
                "Sab minimize kar diya.",
                "hi",
                True,
            )


        if "maximize" in command or "restore" in command:

            subprocess.Popen(
                'powershell -command "(New-Object -ComObject Shell.Application).UndoMinimizeALL()"',
                shell=True
            )

            return (
                "Restore kar diya.",
                "hi",
                True,
            )


        if "screenshot" in command or "screen shot" in command:

            subprocess.Popen(
                "explorer ms-screenclip:",
                shell=True
            )

            return (
                "Screenshot tool khol diya.",
                "hi",
                True,
            )


        return None


    def launch(self, name):

        app = self.find_app(name)


        folders = {

            "downloads":
                str(Path.home() / "Downloads"),

            "documents":
                str(Path.home() / "Documents"),

            "desktop":
                str(Path.home() / "Desktop"),

            "pictures":
                str(Path.home() / "Pictures"),

            "videos":
                str(Path.home() / "Videos"),

            "music":
                str(Path.home() / "Music"),

        }


        if app in folders:

            subprocess.Popen(
                f'explorer "{folders[app]}"',
                shell=True
            )

            return (
                f"{app} khol diya.",
                "hi",
                True,
            )

        commands = {
            'calculator': 'calc.exe',
            'notepad': 'notepad.exe',
            'paint': 'mspaint.exe',

            'whatsapp':
                'start shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App',
            'explorer': 'explorer.exe',
            'cmd': 'cmd.exe',
            'task manager': 'taskmgr.exe',
        }

        office_apps = {
            'excel': 'Microsoft.Office.EXCEL.EXE.15',
            'word': 'Microsoft.Office.WINWORD.EXE.15',
            'powerpoint': 'Microsoft.Office.POWERPNT.EXE.15',
        }

        try:

            if app in office_apps:
                subprocess.Popen(
                    f'start shell:AppsFolder\\{office_apps[app]}',
                    shell=True
                )
                return (
                    f'{app} khol diya.',
                    'hi',
                    True,
                )

            if app in commands:
                subprocess.Popen(commands[app])
                return (
                    f'{app} khol diya.',
                    'hi',
                    True,
                )

            if app == 'chrome':
                webbrowser.open('https://www.google.com')
                return ('Chrome khol diya.', 'hi', True)

        except Exception as exc:
            print('MJ APP ERROR:', exc)

        return (
            f'{app} nahi mila.',
            'hi',
            False,
        )

