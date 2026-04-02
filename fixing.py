import customtkinter as ctk
import json
import os
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

import sys

# Veriyi her zaman .exe'nin yanındaki klasöre kaydet
if getattr(sys, 'frozen', False):
    # PyInstaller ile build edilmişse → exe'nin bulunduğu klasör
    app_dir = os.path.dirname(sys.executable)
else:
    # Normal Python ile çalışıyorsa → script'in bulunduğu klasör
    app_dir = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(app_dir, "su_takip_data.json")


# ── Veri ──────────────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"musteriler": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_telefon(tel):
    """05546946469 → 0554-694-64-69"""
    temiz = ''.join(filter(str.isdigit, tel))
    if len(temiz) >= 10:
        if len(temiz) == 10:
            return f"{temiz[:3]}-{temiz[3:6]}-{temiz[6:8]}-{temiz[8:]}"
        elif len(temiz) == 11 and temiz.startswith('0'):
            return f"{temiz[:4]}-{temiz[4:7]}-{temiz[7:9]}-{temiz[9:]}"
    return tel

def tarih_fmt(iso):
    gunler = ["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"]
    aylar = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} {aylar[d.month]} {gunler[d.weekday()]}"
    except Exception:
        return iso


# ── Yeni Müşteri Penceresi ────────────────────────────────────────────────────
class YeniMusteriPenceresi(ctk.CTkToplevel):
    def __init__(self, parent, musteri=None, kaydet_cb=None):
        super().__init__(parent)
        self.musteri = musteri
        self.kaydet_cb = kaydet_cb
        self.title("Müşteri Bilgileri")
        self.geometry("430x480")
        self.minsize(430, 480)
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
        ctk.CTkLabel(self, text=baslik,
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 8))

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

        ctk.CTkButton(fr, text="✅  Kaydı Tamamlamak için dokun", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
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
            self.musteri.update({"isim": isim, "soyisim": soyisim,
                                 "telefon": telefon, "adres": adres})
        else:
            self.musteri = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "isim": isim,
                "soyisim": soyisim,
                "telefon": telefon,
                "adres": adres,
                "kayit_tarihi": date.today().isoformat(),
                "aktif": True,
                "siparisler": [],
            }

        if self.kaydet_cb:
            self.kaydet_cb(self.musteri)
        self.destroy()


# ── Sipariş Ver Penceresi ─────────────────────────────────────────────────────
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
        ctk.CTkLabel(self, text="💧 Sipariş Ver",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(22, 4))
        ctk.CTkLabel(self, text=ad,
                     font=ctk.CTkFont(size=14), text_color="#7eb8f7").pack()

        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=30)

        ctk.CTkLabel(fr, text="Kaç damacana? (max 10)",
                     font=ctk.CTkFont(size=13)).pack(anchor="w", pady=(18, 4))
        self.dam_e = ctk.CTkEntry(fr, placeholder_text="1-10 (örn: 3)", height=40,
                                  font=ctk.CTkFont(size=15))
        self.dam_e.pack(fill="x")
        self.dam_e.focus()
        self.dam_e.bind("<Return>", lambda e: self._onayla())

        ctk.CTkButton(fr, text="✅  Siparişi Onayla", height=44,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._onayla).pack(pady=18, fill="x")

    def _onayla(self):
        try:
            adet = int(self.dam_e.get().strip())
            if adet < 1 or adet > 10:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Hata", "1-10 arası damacana girin!", parent=self)
            return

        # Pazar günlerini atlayarak program oluştur
        program = []
        gun = date.today()
        while len(program) < adet:
            if gun.weekday() != 6:  # 6 = Pazar
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


# ── Sipariş Kartı ─────────────────────────────────────────────────────────────
class SiparisKarti(ctk.CTkFrame):
    def __init__(self, parent, musteri, siparis, guncelle_cb, **kw):
        super().__init__(parent, corner_radius=14, **kw)
        self.musteri = musteri
        self.siparis = siparis
        self.guncelle_cb = guncelle_cb
        self._build()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        m = self.musteri
        s = self.siparis
        pg = s.get("program", [])
        tum_tamam = bool(pg) and all(g["teslim"] for g in pg)

        # Üst satır
        ust = ctk.CTkFrame(self, fg_color="transparent")
        ust.pack(fill="x", padx=14, pady=(12, 4))

        isim_renk = "#6b7280" if tum_tamam else "white"
        ctk.CTkLabel(ust, text=f"{m['isim']} {m['soyisim']}",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=isim_renk).pack(side="left")

        teslim_n = sum(1 for g in pg if g["teslim"])
        ctk.CTkLabel(ust, text=f"{teslim_n}/{s['toplam_dam']} 🪣",
                     font=ctk.CTkFont(size=13), text_color="#94a3b8").pack(side="right")

        ctk.CTkLabel(self,
                     text=f"📞 {format_telefon(m['telefon'])}   🗓️ Sipariş: {tarih_fmt(s['olusturma'])}",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#60a5fa").pack(anchor="w", padx=14, pady=(0, 6))

        # Program listesi
        liste = ctk.CTkFrame(self, fg_color=("#0f172a", "#0f172a"), corner_radius=10)
        liste.pack(fill="x", padx=14, pady=(0, 12))

        ctk.CTkLabel(liste, text="Teslimat Programı",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkFrame(liste, height=1, fg_color="#1e3a5f").pack(fill="x", padx=12, pady=(0, 4))

        for idx, gun in enumerate(pg):
            self._satir(liste, idx, gun)

        if tum_tamam:
            ctk.CTkLabel(self, text="🎉 Sipariş tamamlandı!",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#4ade80").pack(pady=(0, 8))

    def _satir(self, parent, idx, gun):
        teslim = gun["teslim"]
        tarih = gun["tarih"]
        bugun = date.today().isoformat()
        gecmis = tarih < bugun
        bugun_mu = tarih == bugun

        if teslim:
            bg = ("#052e16", "#052e16")
        elif bugun_mu:
            bg = ("#0c2340", "#0c2340")
        elif gecmis:
            bg = ("#1f0a0a", "#1f0a0a")
        else:
            bg = ("#111827", "#111827")

        satir = ctk.CTkFrame(parent, fg_color=bg, corner_radius=8)
        satir.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(satir, text=f"{idx+1}.", font=ctk.CTkFont(size=12),
                     text_color="#64748b", width=24).pack(side="left", padx=(10, 4), pady=8)

        if teslim:
            etiket = "✅ " + tarih_fmt(tarih)
        elif bugun_mu:
            etiket = "🔵 " + tarih_fmt(tarih) + "  (Bugün)"
        elif gecmis:
            etiket = "🔴 " + tarih_fmt(tarih) + "  (Gecikmiş!)"
        else:
            etiket = "📅 " + tarih_fmt(tarih)

        renk = "#4ade80" if teslim else ("#f87171" if gecmis and not teslim else "white")
        ctk.CTkLabel(satir, text=etiket,
                     font=ctk.CTkFont(size=13, overstrike=teslim),
                     text_color=renk).pack(side="left", padx=4)

        ctk.CTkLabel(satir, text="🪣 1",
                     font=ctk.CTkFont(size=11), text_color="#475569").pack(side="left", padx=6)

        if not teslim:
            ctk.CTkButton(satir, text="Teslim Et", width=90, height=28,
                          fg_color="#1d4ed8", hover_color="#1e40af",
                          font=ctk.CTkFont(size=12),
                          command=lambda g=gun: self._teslim_et(g)).pack(side="right", padx=10, pady=6)
        else:
            ctk.CTkLabel(satir, text="Teslim Edildi ✓",
                         font=ctk.CTkFont(size=11),
                         text_color="#4ade80").pack(side="right", padx=12)

    def _teslim_et(self, gun):
        gun["teslim"] = True
        self._build()                    # Kartı yenile
        self.guncelle_cb()               # Ana listeyi güncelle (tamamlananlar kalksın)


# ── Ana Uygulama ──────────────────────────────────────────────────────────────
class SuTakipApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("💧 Damacana Su Takip v1")
        self.geometry("1080x740")
        self.minsize(820, 560)
        self.data = load_data()
        self.filtre = "aktif"
        self._mod = "dark"
        self._kart_cache = {}
        self._build_ui()
        self._listele()

    def _build_ui(self):
        # Sol panel
        self.sol = ctk.CTkFrame(self, width=265, corner_radius=0, fg_color=("#111827", "#111827"))
        self.sol.pack(side="left", fill="y")
        self.sol.pack_propagate(False)

        logo_satir = ctk.CTkFrame(self.sol, fg_color="transparent")
        logo_satir.pack(fill="x", padx=12, pady=(18, 0))

        ctk.CTkLabel(logo_satir, text="💧  Su Takip",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(side="left")

        self.mod_btn = ctk.CTkButton(
            logo_satir, text="☀️", width=36, height=30,
            fg_color="transparent", border_width=1, border_color="#374151",
            font=ctk.CTkFont(size=14),
            command=self._mod_degistir
        )
        self.mod_btn.pack(side="right")

        ctk.CTkLabel(self.sol, text=date.today().strftime("%d.%m.%Y"),
                     font=ctk.CTkFont(size=11), text_color="#4b5563").pack(anchor="w", padx=16, pady=(2, 12))

        ctk.CTkButton(self.sol, text="➕  Yeni Müşteri", height=40,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._yeni_musteri).pack(padx=14, pady=(0, 10), fill="x")

        # Müşteriler
        ctk.CTkFrame(self.sol, height=1, fg_color="#1f2937").pack(fill="x", padx=14, pady=(0, 8))
        ctk.CTkLabel(self.sol, text="MÜŞTERİLER",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#4b5563").pack(anchor="w", padx=16, pady=(0, 4))

        self.musteri_arama = ctk.CTkEntry(self.sol, placeholder_text="🔍 İsim ara...", height=32)
        self.musteri_arama.pack(fill="x", padx=14, pady=(0, 4))
        self.musteri_arama.bind("<KeyRelease>", lambda e: self._musteri_listele())

        self.musteri_scroll = ctk.CTkScrollableFrame(self.sol, fg_color="transparent", height=240)
        self.musteri_scroll.pack(fill="x", padx=6, pady=(0, 4))

        # Sipariş Filtreleri (Gecikmiş kaldırıldı)
        ctk.CTkFrame(self.sol, height=1, fg_color="#1f2937").pack(fill="x", padx=14, pady=8)
        ctk.CTkLabel(self.sol, text="SİPARİŞLER",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color="#4b5563").pack(anchor="w", padx=16, pady=(0, 4))

        self._filtre_butonlari = {}
        menu = [
            ("📋  Aktif", "aktif"),
            ("✅  Tamamlanan", "tamamlanan"),
            ("📦  Tümü", "hepsi"),
        ]
        for metin, filtre in menu:
            btn = ctk.CTkButton(
                self.sol, text=metin, height=32, anchor="w",
                fg_color="transparent", border_width=1, border_color="#1f2937",
                font=ctk.CTkFont(size=12),
                command=lambda f=filtre: self._filtre_sec(f)
            )
            btn.pack(padx=14, pady=2, fill="x")
            self._filtre_butonlari[filtre] = btn
        self._filtre_btn_guncelle()

        # İstatistik (Bugün teslim kaldırıldı)
        ist = ctk.CTkFrame(self.sol, fg_color="#1e293b", corner_radius=10)
        ist.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(ist, text="Özet", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#94a3b8").pack(anchor="w", padx=10, pady=(8, 2))
        self.istat_lbl = ctk.CTkLabel(ist, text="", font=ctk.CTkFont(size=11),
                                      text_color="#cbd5e1", justify="left")
        self.istat_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # Sağ panel
        sag = ctk.CTkFrame(self, fg_color="transparent")
        sag.pack(side="right", fill="both", expand=True, padx=12, pady=12)

        ust_bar = ctk.CTkFrame(sag, fg_color="transparent")
        ust_bar.pack(fill="x", pady=(0, 10))

        self.baslik_lbl = ctk.CTkLabel(ust_bar, text="Aktif Siparişler",
                                       font=ctk.CTkFont(size=19, weight="bold"))
        self.baslik_lbl.pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(sag, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._musteri_listele()

    def _mod_degistir(self):
        if self._mod == "dark":
            self._mod = "light"
            ctk.set_appearance_mode("light")
            self.mod_btn.configure(text="🌙")
        else:
            self._mod = "dark"
            ctk.set_appearance_mode("dark")
            self.mod_btn.configure(text="☀️")

    def _filtre_btn_guncelle(self):
        for filtre, btn in self._filtre_butonlari.items():
            if filtre == self.filtre:
                btn.configure(fg_color="#1d4ed8", border_color="#1d4ed8")
            else:
                btn.configure(fg_color="transparent", border_color="#1f2937")

    def _musteri_listele(self):
        for w in self.musteri_scroll.winfo_children():
            w.destroy()

        q = self.musteri_arama.get().lower().strip()
        musteriler = self.data["musteriler"]
        if q:
            musteriler = [m for m in musteriler
                          if q in m["isim"].lower() or q in m["soyisim"].lower()
                          or q in m.get("telefon", "").lower()]

        if not musteriler:
            ctk.CTkLabel(self.musteri_scroll, text="Kayıt yok",
                         font=ctk.CTkFont(size=11), text_color="#4b5563").pack(pady=8)
            return

        for m in musteriler:
            self._musteri_satiri(m)

    def _musteri_satiri(self, m):
        satir = ctk.CTkFrame(self.musteri_scroll, fg_color="#1e293b", corner_radius=8)
        satir.pack(fill="x", pady=3, padx=4)

        # Grid: butonlar her zaman sağda sabit görünür, isim kalan alanı alır
        satir.columnconfigure(0, weight=1)
        satir.columnconfigure(1, weight=0)
        satir.columnconfigure(2, weight=0)

        sol = ctk.CTkFrame(satir, fg_color="transparent")
        sol.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)

        ctk.CTkLabel(sol, text=f"{m['isim']} {m['soyisim']}",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w", wraplength=90).pack(anchor="w", fill="x")
        ctk.CTkLabel(sol, text=m.get("telefon", ""),
                     font=ctk.CTkFont(size=11), text_color="#64748b",
                     anchor="w").pack(anchor="w")

        ctk.CTkButton(satir, text="🗑️ Sil", width=52, height=28,
                      fg_color="#ef4444", hover_color="#dc2626",
                      font=ctk.CTkFont(size=11),
                      command=lambda ms=m: self._musteri_sil(ms)).grid(row=0, column=1, padx=(0, 4), pady=8)
        ctk.CTkButton(satir, text="📦", width=34, height=28,
                      fg_color="#1d4ed8", hover_color="#1e40af",
                      font=ctk.CTkFont(size=11),
                      command=lambda ms=m: self._siparis_ver(ms)).grid(row=0, column=2, padx=(0, 6), pady=8)

    # ── Sipariş işlemleri ─────────────────────────────────────────────────────
    def _yeni_musteri(self):
        YeniMusteriPenceresi(self, kaydet_cb=self._musteri_kaydet)

    def _musteri_kaydet(self, musteri):
        if musteri not in self.data["musteriler"]:
            self.data["musteriler"].append(musteri)
        save_data(self.data)
        self._musteri_listele()
        self._listele()

    def _siparis_ver(self, musteri):
        SiparisVer(self, musteri, kaydet_cb=lambda: (save_data(self.data), self._listele()))

    def _veri_guncelle(self):
        save_data(self.data)
        self._listele()          # Tamamlanan siparişler hemen kalksın

    def _musteri_sil(self, musteri):
        if messagebox.askyesno("Silme Onayı", f"{musteri['isim']} {musteri['soyisim']} ve tüm siparişlerini silmek istediğinizden emin misiniz?"):
            self.data["musteriler"] = [m for m in self.data["musteriler"] if m["id"] != musteri["id"]]
            save_data(self.data)
            self._musteri_listele()
            self._listele()

    def _filtre_sec(self, filtre):
        basliklar = {
            "aktif": "Aktif Siparişler",
            "tamamlanan": "Tamamlanan Siparişler",
            "hepsi": "Tüm Siparişler",
        }
        self.filtre = filtre
        self.baslik_lbl.configure(text=basliklar.get(filtre, ""))
        self._filtre_btn_guncelle()
        self._listele()

    def _siparis_tamam_mi(self, s):
        pg = s.get("program", [])
        return bool(pg) and all(g["teslim"] for g in pg)

    # ── Ana liste ─────────────────────────────────────────────────────────────
    def _listele(self):
        ciftler = []
        for m in self.data["musteriler"]:
            for s in m.get("siparisler", []):
                tamam = self._siparis_tamam_mi(s)

                if self.filtre == "aktif" and tamam:
                    continue
                if self.filtre == "tamamlanan" and not tamam:
                    continue
                ciftler.append((m, s))

        goster_ids = {s["id"] for _, s in ciftler}

        # Eski kartları temizle
        for sid in list(self._kart_cache):
            if sid not in goster_ids:
                self._kart_cache.pop(sid).destroy()

        if not ciftler:
            for w in self.scroll.winfo_children():
                if isinstance(w, ctk.CTkLabel):
                    w.destroy()
            ctk.CTkLabel(self.scroll, text="📭  Gösterilecek sipariş yok.",
                         font=ctk.CTkFont(size=14), text_color="#4b5563").pack(pady=60)
            self._istatistik()
            return

        # Boş mesajı temizle
        for w in self.scroll.winfo_children():
            if isinstance(w, ctk.CTkLabel):
                w.destroy()

        for i, (_, s) in enumerate(ciftler):
            sid = s["id"]
            if sid not in self._kart_cache:
                kart = SiparisKarti(self.scroll, _, s, guncelle_cb=self._veri_guncelle)  # _ = musteri
                self._kart_cache[sid] = kart

            kart = self._kart_cache[sid]
            son_mu = (i == len(ciftler) - 1)
            kart.pack(fill="x", padx=4, pady=(6, 24 if son_mu else 6))

        self._istatistik()

    def _istatistik(self):
        tum_siparisler = [(m, s) for m in self.data["musteriler"]
                          for s in m.get("siparisler", [])]
        aktif = sum(1 for _, s in tum_siparisler if not self._siparis_tamam_mi(s))
        tamam = sum(1 for _, s in tum_siparisler if self._siparis_tamam_mi(s))

        self.istat_lbl.configure(
            text=f"⏳ Aktif sipariş: {aktif}\n"
                 f"✅ Tamamlanan: {tamam}"
        )


# ── Başlat ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SuTakipApp()
    app.mainloop()