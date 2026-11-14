# di-software 27

Kullanıcının yüklediği **di-software 27.zip** sürümünün 3 yazılımlı yapısı ve Liquid Glass arayüzü korunmuştur. Kaldırılan projeler geri eklenmedi.

## Siteyi çalıştırma

Windows'ta `BASLAT.bat` dosyasını aç. Python 3 kurulu olmalı, Flask kurulu değilse BAT dosyası `requirements.txt` üzerinden yükler.

Komutla çalıştırmak istersen:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Site: http://127.0.0.1:5080

## Kullanıcı ne görür?

Üç program: AtoAI 27, di-browser, pydi-ide. Ziyaretçi projeyi açıp **İndir** butonuna bastığında dosya tarayıcıda yeni site açılmadan indirilir. İndirme bağlantısı sitenin kendi `/indir/<proje>/<surum>` adresidir. Proje listesi API'sinde ve web sayfasında haricî bağlantılar gösterilmez. Ziyaretçinin kaynak koda erişim menüsü, yönetici paneli veya üyelik zorunluluğu yoktur.

## İndirmeler nasıl çalışıyor?

**Önemli: İndirme dosyaları ZIP içinde tutulmaz.** Flask, `data/projects.json` dosyasında belirtilen özel sunucu tarafı EXE bağlantısını kullanır. Sunucu dosyayı orijinal sağlayıcıdan parça parça alır ve indiren kişinin tarayıcısına **kendi adresi üzerinden** gönderir. Dolayısıyla normal indirme akışında GitHub web sayfası veya adres çubuğu açılmaz.

EXE'ler şu dosya adlarıyla indirilir:

| Yazılım | İndirilen dosya |
| --- | --- |
| AtoAI 27 | `di-ato.27.exe` |
| di-browser | `di-browser.exe` |
| pydi-ide | `pydi-ide.exe` |

Yayın dosyasını değiştirmek için `data/projects.json` dosyasında ilgili `releases[].url` adresini değiştirip sunucuyu yeniden başlat. Bu sürümde **doğrudan indirilebilir GitHub Release ikili dosyaları** proxy üzerinden aktarılır. `dosya.co` gibi indirme sayfası sunan bağlantılar otomatik EXE akışı olmadığı için bu yöntemle desteklenmez; yeni bir sağlayıcı için ayrıca entegrasyon gerekir.

**Barındırma bilgisi:** İndirilen dosyanın bütün baytları Flask sunucusunun üzerinden geçer. Dolayısıyla internete açıldığında sunucunun çıkış trafiği ve bağlantı süresi tüketilir; büyük indirmeler ve yoğun ziyaretlerde daha güçlü barındırma gerekir. Kullanıcıya gösterilen indirme adresinden orijinal sağlayıcı görünmez, ancak teknik olarak yazılımın başka yerlerde de yayımlandığı hiçbir şekilde gizlenemez veya garanti edilemez.

Sadece `BASLAT.bat` çalıştırmak siteyi internet üzerinde yayınlamaz; bunun için ayrıca Flask uygulamasını barındırman gerekir.

## Denetimler

- `python -m pytest -q`
- Flask yüklü değilse Flask uç testleri atlanır, indirme akış testleri yine çalışır.

## 120 Hz ekranlar için Liquid Glass optimizasyonu

Bu paketin tasarımı korunur: dört büyük floating pencere gerçek `backdrop-filter`
ile şeffaf/bulanık kalır; küçük kartlar ve butonlar aynı görünümü transparan
gradient/kenar parlaklıklarıyla verir, ancak büyük arka plan katmanlarını tekrar
tekrar bulanıklaştırmaz. Panel kaydırma ve hover hareketlerinde **yalnızca
`transform` ve `opacity` animasyonu** yapılır. Yalnızca geçiş sırasında GPU
katmanı ipucu verilir; boşta sonsuz animasyon çalıştırılmaz. Mobilde cam bulanıklığı
11px'e düşer, efekt kapatılmaz. Azaltılmış hareket sistem tercihi desteklenir.

**Hedef 120 FPS**, fakat her cihazda sabit 120 FPS garanti edilemez; ekranın 120 Hz
olması ve tarayıcı/ekran kartının uygun olması gerekir. Render sunucu gecikmesini
değiştirir, tarayıcının çizim kapasitesini değiştirmez.

## Render'da yayınlama

1. `di-software 27` klasöründeki dosyaları özel/public Git deposuna yükle.
2. Render'da **New > Blueprint** ile bu depodaki `render.yaml` dosyasını seç.
3. Alternatif olarak **New > Web Service** kurarken Build Command olarak
   `pip install -r requirements-render.txt` ve Start Command olarak
   `gunicorn --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 300 app:app`
   gir.
4. `/health` adresiyle sunucuyu kontrol et; site kök adreste açılır.

Üç EXE hâlâ GitHub Releases kaynaklarından **Flask proxy** aracılığıyla aktarılır:
butonlar `/indir/<slug>/<surum>` şeklindedir. Kaynak bağlantılar HTML/JS'ye
yazılmaz; fakat ağ geçidi üzerinden büyük indirmeler Render'ın bant genişliği,
zaman aşımı ve olası plan limitlerine tabidir. 120 FPS hedefi Render'a geçmekle
kendiliğinden gerçekleşmez.

## Telefon, tablet, bilgisayar görünümü (yeni)

Üst menüdeki **Ekran / Otomatik** düğmesi, açılan Liquid Glass penceresinde
**Otomatik, Telefon, Tablet, Bilgisayar** seçeneklerini sunar. Otomatik mod
ekran genişliğine göre masaüstünde üç sütun, telefonda iki sütun düzenini
uygular. Diğer seçimler tasarımı o cihaz düzenine çevirir. Seçim tarayıcıda
`localStorage` ile saklanır; Render üzerinde hesap açmak veya giriş yapmak gerekmez.
Dar ekranlarda geniş masaüstü düzeni gerektiğinde okunabilirlik için uyarlanır.

Bu, tarayıcıdaki görünüm tercihidir; fiziksel ekranın yenileme hızını (Hz)
değiştirmez. Liquid Glass şeffaflığı tüm cihaz modlarında korunur.


Ekran duzeni otomatik: telefon, tablet ve masaustu icin CSS media query kullanilir. Manuel cihaz secici yoktur.
120 FPS hedeflenir, cihaz ve tarayiciya bagli olarak garanti edilmez.
