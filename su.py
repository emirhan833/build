import customtkinter as ctk
import json
import os
from datetime import datetime, date, timedelta
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DATA_FILE = "su_takip_data.json"

# ── Yardımcı Fonksiyonlar ───────────────────────────────────────────────────
def format_telefon(tel):
    """05321234567 → 0532-123-45-67"""
    temiz = ''.join(filter(str.isdigit, tel))
    if len(temiz) == 10:
        return f"{temiz[:3]}-{temiz[3:6]}-{temiz[6:8]}-{temiz[8:]}"
    elif len(temiz) == 11 and temiz.startswith("0"):
        return f"{temiz[:4]}-{temiz[4:7]}-{temiz[7:9]}-{temiz[9:]}"
    return tel

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"musteriler": []}
    return {"musteriler": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def tarih_fmt(iso):
    gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
    aylar = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} {aylar[d.month]} {gunler[d.weekday()]}"
    except: return iso

# ── UI Bileşenleri ──────────────────────────────────────────────────────────
class YeniMusteriPenceresi(ctk.CTkToplevel):
    def __init__(self, parent, musteri=None, kaydet_cb=None):
        super().__init__(parent)
        self.musteri = musteri
        self.kaydet_cb = kaydet_cb
        self.title("Müşteri Bilgileri")
        self.geometry("400x500")
        self.after(10, self.lift) # Fokus sorunu için
        self._build()

    def _build(self):
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=20, pady=20)

        self.isim_e = ctk.CTkEntry(fr, placeholder_text="İsim"); self.isim_e.pack(fill="x", pady=5)
        self.soyisim_e = ctk.CTkEntry(fr, placeholder_text="Soyisim"); self.soyisim_e.pack(fill="x", pady=5)
        self.tel_e = ctk.CTkEntry(fr, placeholder_text="Telefon"); self.tel_e.pack(fill="x", pady=5)
        self.adres_e = ctk.CTkTextbox(fr, height=60); self.adres_e.pack(fill="x", pady=5)

        ctk.CTkButton(fr, text="Kaydet", command=self._kaydet).pack(fill="x", pady=10)

    def _kaydet(self):
        if not self.isim_e.get(): return
        data = {
            "id": self.musteri["id"] if self.musteri else datetime.now().strftime("%Y%m%d%H%M%S"),
            "isim": self.isim_e.get(),
            "soyisim": self.soyisim_e.get(),
            "telefon": format_telefon(self.tel_e.get()),
            "adres": self.adres_e.get("0.0", "end").strip(),
            "siparisler": self.musteri["siparisler"] if self.musteri else []
        }
        self.kaydet_cb(data)
        self.destroy()

class SiparisKarti(ctk.CTkFrame):
    def __init__(self, parent, musteri, siparis, guncelle_cb):
        super().__init__(parent, fg_color="#1e293b", corner_radius=12)
        self.musteri, self.siparis, self.guncelle_cb = musteri, siparis, guncelle_cb
        self._build()

    def _build(self):
        for w in self.winfo_children(): w.destroy()
        ctk.CTkLabel(self, text=f"{self.musteri['isim']} {self.musteri['soyisim']}", font=("Arial", 14, "bold")).pack(pady=5)
        ctk.CTkLabel(self, text=f"📞 {self.musteri['telefon']}", text_color="#60a5fa").pack()
        
        for gun in self.siparis.get("program", []):
            f = ctk.CTkFrame(self, fg_color="#0f172a")
            f.pack(fill="x", padx=10, pady=2)
            txt = f"{'✅' if gun['teslim'] else '⏳'} {tarih_fmt(gun['tarih'])}"
            ctk.CTkLabel(f, text=txt).pack(side="left", padx=5)
            if not gun["teslim"]:
                ctk.CTkButton(f, text="Teslim Et", width=60, height=20, command=lambda g=gun: self._teslim(g)).pack(side="right", padx=5)

    def _teslim(self, gun):
        gun["teslim"] = True
        self.guncelle_cb()
        self._build()

# ── Ana Uygulama ───────────────────────────────────────────────────────────
class SuTakipApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("💧 Damacana Takip")
        self.geometry("1000x650")
        self.data = load_data()
        self._build_ui()
        self._listele()

    def _build_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkButton(self.sidebar, text="➕ Yeni Müşteri", command=self._yeni_musteri).pack(pady=10, padx=10)
        self.stats_lbl = ctk.CTkLabel(self.sidebar, text="Özet", font=("Arial", 16, "bold"))
        self.stats_lbl.pack(pady=20)

        # Ana Alan
        self.main_scroll = ctk.CTkScrollableFrame(self)
        self.main_scroll.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def _listele(self):
        for w in self.main_scroll.winfo_children(): w.destroy()
        
        aktif_siparis_sayisi = 0
        for m in self.data["musteriler"]:
            for s in m.get("siparisler", []):
                if not all(g["teslim"] for g in s["program"]):
                    SiparisKarti(self.main_scroll, m, s, self._veri_kaydet).pack(fill="x", pady=5)
                    aktif_siparis_sayisi += 1
        
        self.stats_lbl.configure(text=f"Aktif Sipariş: {aktif_siparis_sayisi}")

    def _yeni_musteri(self):
        YeniMusteriPenceresi(self, kaydet_cb=self._musteri_kaydet)

    def _musteri_kaydet(self, yeni_m):
        self.data["musteriler"].append(yeni_m)
        self._veri_kaydet()
        self._siparis_ekle_pencere(yeni_m)

    def _siparis_ekle_pencere(self, m):
        # Basitçe 1 sipariş oluşturur (Geliştirilebilir)
        dialog = ctk.CTkInputDialog(text="Kaç damacana?", title="Sipariş")
        adet_str = dialog.get_input()
        if adet_str and adet_str.isdigit():
            adet = int(adet_str)
            prog = [{"tarih": (date.today() + timedelta(days=i)).isoformat(), "teslim": False} for i in range(adet)]
            m["siparisler"].append({"id": str(datetime.now().timestamp()), "program": prog})
            self._veri_kaydet()
            self._listele()

    def _veri_kaydet(self):
        save_data(self.data)

if __name__ == "__main__":
    app = SuTakipApp()
    app.mainloop()