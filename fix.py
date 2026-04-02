import customtkinter as ctk
import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys

# ¦¦ DOSYA YOLU AYARI (Kalıcı Kayıt İçin) ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
# Kullanıcının "Belgeler" klasöründe bir klasör oluşturur. 
# Bu yöntem, exe yapıldığında verilerin silinmesini engeller.
home_dir = Path.home()
app_data_dir = home_dir / "Documents" / "SuTakipSistemi"
app_data_dir.mkdir(parents=True, exist_ok=True) 

DATA_FILE = str(app_data_dir / "su_takip_data.json")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ¦¦ Veri İşlemleri ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if not content:
                    return {"musteriler": []}
                return json.loads(content)
        except Exception:
            return {"musteriler": []}
    return {"musteriler": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_telefon(tel):
    temiz = ''.join(filter(str.isdigit, tel))
    if len(temiz) >= 10:
        if len(temiz) == 10:
            return f"{temiz[:3]}-{temiz[3:6]}-{temiz[6:8]}-{temiz[8:]}"
        elif len(temiz) == 11 and temiz.startswith('0'):
            return f"{temiz[:4]}-{temiz[4:7]}-{temiz[7:9]}-{temiz[9:]}"
    return tel

def tarih_fmt(iso):
    gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]
    aylar = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} {aylar[d.month]} {gunler[d.weekday()]}"
    except Exception:
        return iso

# ¦¦ Yeni Müşteri Penceresi ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
class YeniMusteriPenceresi(ctk.CTkToplevel):
    def __init__(self, parent, musteri=None, kaydet_cb=None):
        super().__init__(parent)
        self.musteri = musteri
        self.kaydet_cb = kaydet_cb
        self.title("Müşteri Bilgileri")
        self.geometry("430x480")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build()
        if musteri:
            self.isim_e.insert(0, musteri.get("isim", ""))
            self.soyisim_e.insert(0, musteri.get("soyisim", ""))
            self.telefon_e.insert(0, musteri.get("telefon", ""))
            self.adres_e.insert("0.0", musteri.get("adres", ""))

    def _build(self):
        baslik = "Müşteriyi Düzenle" if self.musteri else "Yeni Müşteri Ekle"
        ctk.CTkLabel(self, text=baslik, font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 8))
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        def alan(lbl, ph):
            ctk.CTkLabel(fr, text=lbl, font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(8, 2))
            e = ctk.CTkEntry(fr, placeholder_text=ph, height=38)
            e.pack(fill="x")
            return e

        self.isim_e = alan("İsim *", "")
        self.soyisim_e = alan("Soyisim *", "")
        self.telefon_e = alan("Telefon *", "Örn: 0532 000 0000")

        ctk.CTkLabel(fr, text="Adres (isteğe bağlı)", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(8, 2))
        self.adres_e = ctk.CTkTextbox(fr, height=55)
        self.adres_e.pack(fill="x")

        ctk.CTkButton(fr, text="?  Kaydı Tamamla", height=44, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._kaydet).pack(fill="x", pady=(18, 0))

    def _kaydet(self):
        isim = self.isim_e.get().strip()
        soyisim = self.soyisim_e.get().strip()
        telefon = self.telefon_e.get().strip()
        adres = self.adres_e.get("1.0", "end-1c").strip()

        if not isim or not soyisim or not telefon:
            messagebox.showwarning("Eksik Bilgi", "İsim, soyisim ve telefon zorunludur!", parent=self)
            return

        if self.musteri:
            self.musteri.update({"isim": isim, "soyisim": soyisim, "telefon": telefon, "adres": adres})
        else:
            self.musteri = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "isim": isim, "soyisim": soyisim, "telefon": telefon, "adres": adres,
                "kayit_tarihi": date.today().isoformat(), "aktif": True, "siparisler": [],
            }

        if self.kaydet_cb:
            self.kaydet_cb(self.musteri)
        self.destroy()

# ¦¦ Sipariş Ver Penceresi ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
class SiparisVer(ctk.CTkToplevel):
    def __init__(self, parent, musteri, kaydet_cb):
        super().__init__(parent)
        self.musteri = musteri
        self.kaydet_cb = kaydet_cb
        self.title("Sipariş Ver")
        self.geometry("360x270")
        self.resizable(False, False)
        self.grab_set()
        self.focus()
        self._build()

    def _build(self):
        ad = f"{self.musteri['isim']} {self.musteri['soyisim']}"
        ctk.CTkLabel(self, text="?? Sipariş Ver", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(22, 4))
        ctk.CTkLabel(self, text=ad, font=ctk.CTkFont(size=14), text_color="#7eb8f7").pack()
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=30)
        ctk.CTkLabel(fr, text="Kaç damacana? (max 10)", font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(18, 4))
        self.dam_e = ctk.CTkEntry(fr, placeholder_text="1-10", height=40)
        self.dam_e.pack(fill="x")
        self.dam_e.focus()
        self.dam_e.bind("<Return>", lambda e: self._onayla())
        ctk.CTkButton(fr, text="?  Siparişi Onayla", height=44, font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._onayla).pack(pady=18, fill="x")

    def _onayla(self):
        try:
            adet = int(self.dam_e.get().strip())
            if adet < 1 or adet > 10: raise ValueError
        except ValueError:
            messagebox.showwarning("Hata", "1-10 arası damacana girin!", parent=self)
            return

        program = []
        gun = date.today()
        while len(program) < adet:
            if gun.weekday() != 6: # Pazar hariç
                program.append({"tarih": gun.isoformat(), "teslim": False})
            gun += timedelta(days=1)

        siparis = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "olusturma": date.today().isoformat(),
            "toplam_dam": adet,
            "program": program,
        }
        self.musteri.setdefault("siparisler", []).append(siparis)
        self.kaydet_cb()
        self.destroy()

# ¦¦ Sipariş Kartı ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
class SiparisKarti(ctk.CTkFrame):
    def __init__(self, parent, musteri, siparis, guncelle_cb, **kw):
        super().__init__(parent, corner_radius=14, **kw)
        self.musteri = musteri
        self.siparis = siparis
        self.guncelle_cb = guncelle_cb
        self._build()

    def _build(self):
        for w in self.winfo_children(): w.destroy()
        m, s = self.musteri, self.siparis
        pg = s.get("program", [])
        tum_tamam = bool(pg) and all(g["teslim"] for g in pg)

        ust = ctk.CTkFrame(self, fg_color="transparent")
        ust.pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(ust, text=f"{m['isim']} {m['soyisim']}", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color="white" if not tum_tamam else "#6b7280").pack(side="left")
        
        teslim_n = sum(1 for g in pg if g["teslim"])
        ctk.CTkLabel(ust, text=f"{teslim_n}/{s['toplam_dam']} ??", font=ctk.CTkFont(size=13), text_color="#94a3b8").pack(side="right")

        ctk.CTkLabel(self, text=f"?? {format_telefon(m['telefon'])}   ??? {tarih_fmt(s['olusturma'])}",
                     font=ctk.CTkFont(size=13), text_color="#60a5fa").pack(anchor="w", padx=14)

        liste = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=10)
        liste.pack(fill="x", padx=14, pady=(8, 12))

        for idx, gun in enumerate(pg):
            self._satir(liste, idx, gun)

    def _satir(self, parent, idx, gun):
        teslim, tarih = gun["teslim"], gun["tarih"]
        bugun = date.today().isoformat()
        
        satir = ctk.CTkFrame(parent, fg_color="#111827" if not teslim else "#052e16", corner_radius=8)
        satir.pack(fill="x", padx=8, pady=3)

        ctk.CTkLabel(satir, text=tarih_fmt(tarih), font=ctk.CTkFont(size=12, overstrike=teslim)).pack(side="left", padx=10, pady=6)
        
        if not teslim:
            ctk.CTkButton(satir, text="Teslim Et", width=80, height=26, command=lambda: self._teslim_et(gun)).pack(side="right", padx=8)
        else:
            ctk.CTkLabel(satir, text="Tamamlandı ?", text_color="#4ade80", font=ctk.CTkFont(size=11)).pack(side="right", padx=10)

    def _teslim_et(self, gun):
        gun["teslim"] = True
        self.guncelle_cb()

# ¦¦ Ana Uygulama ¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
class SuTakipApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("?? Damacana Su Takip v1.1")
        self.geometry("1100x750")
        self.data = load_data()
        self.filtre = "aktif"
        self._kart_cache = {}
        self._build_ui()
        self._listele()

    def _build_ui(self):
        # Sol Panel
        self.sol = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="#111827")
        self.sol.pack(side="left", fill="y")
        self.sol.pack_propagate(False)

        ctk.CTkLabel(self.sol, text="?? Su Takip", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)
        
        ctk.CTkButton(self.sol, text="? Yeni Müşteri", command=self._yeni_musteri).pack(padx=20, pady=10, fill="x")

        self.musteri_arama = ctk.CTkEntry(self.sol, placeholder_text="?? İsim ara...")
        self.musteri_arama.pack(fill="x", padx=20, pady=10)
        self.musteri_arama.bind("<KeyRelease>", lambda e: self._musteri_listele())

        self.musteri_scroll = ctk.CTkScrollableFrame(self.sol, fg_color="transparent", height=300)
        self.musteri_scroll.pack(fill="x", padx=10)

        # Filtre Butonları
        ctk.CTkFrame(self.sol, height=2, fg_color="#1f2937").pack(fill="x", padx=20, pady=20)
        for f in [("?? Aktif", "aktif"), ("? Tamamlanan", "tamamlanan"), ("?? Tümü", "hepsi")]:
            ctk.CTkButton(self.sol, text=f[0], fg_color="transparent", border_width=1, 
                          command=lambda x=f[1]: self._filtre_sec(x)).pack(padx=20, pady=2, fill="x")

        # Sağ Panel
        self.sag = ctk.CTkFrame(self, fg_color="transparent")
        self.sag.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.baslik_lbl = ctk.CTkLabel(self.sag, text="Aktif Siparişler", font=ctk.CTkFont(size=22, weight="bold"))
        self.baslik_lbl.pack(anchor="w", pady=(0, 20))

        self.scroll = ctk.CTkScrollableFrame(self.sag, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def _musteri_listele(self):
        for w in self.musteri_scroll.winfo_children(): w.destroy()
        q = self.musteri_arama.get().lower()
        for m in self.data["musteriler"]:
            if q in m["isim"].lower() or q in m["soyisim"].lower():
                f = ctk.CTkFrame(self.musteri_scroll, fg_color="#1e293b", corner_radius=8)
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=f"{m['isim']} {m['soyisim']}", font=ctk.CTkFont(size=12)).pack(side="left", padx=10, pady=5)
                ctk.CTkButton(f, text="??", width=30, command=lambda x=m: self._siparis_ver(x)).pack(side="right", padx=5)
                ctk.CTkButton(f, text="???", width=30, fg_color="#ef4444", command=lambda x=m: self._musteri_sil(x)).pack(side="right")

    def _yeni_musteri(self):
        YeniMusteriPenceresi(self, kaydet_cb=self._musteri_kaydet)

    def _musteri_kaydet(self, m):
        if m not in self.data["musteriler"]: self.data["musteriler"].append(m)
        save_data(self.data)
        self._musteri_listele()
        self._listele()

    def _siparis_ver(self, m):
        SiparisVer(self, m, kaydet_cb=lambda: (save_data(self.data), self._listele()))

    def _musteri_sil(self, m):
        if messagebox.askyesno("Onay", "Müşteriyi silmek istiyor musunuz?"):
            self.data["musteriler"].remove(m)
            save_data(self.data)
            self._musteri_listele()
            self._listele()

    def _filtre_sec(self, f):
        self.filtre = f
        self.baslik_lbl.configure(text=f.capitalize() + " Siparişler")
        self._listele()

    def _listele(self):
        for w in self.scroll.winfo_children(): w.destroy()
        for m in self.data["musteriler"]:
            for s in m.get("siparisler", []):
                tamam = all(g["teslim"] for g in s.get("program", []))
                if (self.filtre == "aktif" and tamam) or (self.filtre == "tamamlanan" and not tamam):
                    continue
                SiparisKarti(self.scroll, m, s, guncelle_cb=lambda: (save_data(self.data), self._listele())).pack(fill="x", pady=10)

if __name__ == "__main__":
    app = SuTakipApp()
    app.mainloop()
