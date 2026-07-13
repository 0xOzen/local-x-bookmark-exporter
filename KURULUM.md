# Türkçe kurulum ve kullanım

Local X Bookmark Exporter, X bookmark sayfasında görüntülenen kartları JSON, CSV veya Markdown dosyasına aktarır. API anahtarı, haricî sunucu veya hesap bilgisi istemez.

## Güvenlik sınırı

Eklenti:

- X şifreni istemez veya okuyamaz.
- Cookie ya da oturum token'ı toplamaz.
- X'in resmî veya dahili API'sine programlı istek göndermez.
- Haricî sunucu, analiz sistemi veya telemetri kullanmaz.
- Kalıcı `x.com` erişimi istemez.
- Yalnızca eklenti ikonuna bastığın açık sekmede geçici olarak çalışır.
- Dosyayı doğrudan kendi Downloads klasörüne indirir.

Dışa aktarılan dosya özel bookmark verilerini içerebilir. Dosyayı paylaşmadan önce içeriğini kontrol et.

## Chrome'a yükleme

1. GitHub Release asset'i mevcutsa [son GitHub sürümünü](https://github.com/0xOzen/local-x-bookmark-exporter/releases/latest) aç, `local-x-bookmark-exporter-v<version>.zip` dosyasını indir ve ZIP'i çıkar. Alternatif olarak GitHub sayfasında **Code > Download ZIP** seçeneğini kullanabilir veya repoyu Git ile klonlayabilirsin:

   ```bash
   git clone https://github.com/0xOzen/local-x-bookmark-exporter.git
   ```

2. Chrome adres çubuğuna şunu yaz:

   ```text
   chrome://extensions
   ```

3. Sağ üstten **Developer mode** seçeneğini aç.
4. **Load unpacked** düğmesine bas.
5. İçinde `manifest.json` bulunan proje klasörünü seç.
6. İstersen Chrome'un eklenti menüsünden **Yerel X Bookmark Dışa Aktarıcı** eklentisini sabitle.

Developer mode ile yüklenen tüm unpacked eklentiler için Chrome uyarı gösterebilir. Bu normaldir.

## Bookmark dışa aktarma

1. Chrome'da X hesabına giriş yap.
2. Şu sayfayı aç:

   ```text
   https://x.com/i/bookmarks
   ```

3. Bookmark listesinin yüklenmesini bekle.
4. Eklenti ikonuna bas.
5. JSON, CSV veya Markdown biçimini seç.
6. **Dışa aktarmayı başlat** düğmesine bas.
7. Sağ alttaki ilerleme kutusu tamamlandı diyene kadar sekmeyi açık tut.
8. Oluşan dosyayı Downloads klasöründen aç.

JSON, tam veri yapısını koruduğu için yedekleme ve sonraki işlemler için önerilen biçimdir.

## Yerel yardımcı araçlar

Repoda iki isteğe bağlı Python yardımcı aracı da bulunur. Bu araçlar yalnızca yerel dosyalarla çalışır, Python standart kütüphanesini kullanır; X'e istek göndermez, tarayıcı açmaz, yapay zekâ servisi kullanmaz ve export dosyasını değiştirmez.

Yardımcı araçlar için ayrı deterministik kaynak/araç ZIP'i `x-bookmark-companion-tools-v0.1.0.zip` olarak hazırlanır. Bu ZIP Chrome eklentisi değildir; Chrome'a yükleme. Chrome runtime ZIP'i ayrı kalır ve v1.2.0 için `local-x-bookmark-exporter-v1.2.0.zip` adını kullanır.

`DEPENDENCIES.md` ve `sbom.cdx.json`, release-candidate bağımlılık sınırını açıklar: eklenti runtime'ı üçüncü taraf runtime bağımlılığı içermez, yardımcı Python araçları yalnızca standart kütüphane kullanır, Pillow sadece ikonları yeniden üretmek için opsiyonel build aracıdır ve paketlere runtime bağımlılığı olarak eklenmez.

### X Bookmark Archive Doctor

Archive Doctor, JSON export dosyasını başka bir işlemde kullanmadan önce doğrular. Şema sürümünü, metadata sayısını, zorunlu alanları, tekrar eden post ID'lerini, canonical X URL'lerini, UTC timestamp alanlarını, media URL biçimini ve tehlikeli stringleri kontrol eder. `meta.sourcePage` değerini URL olarak ayrıştırır; yalnızca HTTPS `x.com` veya `www.x.com` üzerindeki `/i/bookmarks` ya da `/i/bookmarks/...` route'larını kabul eder. Query string serbesttir; credentials, default olmayan port, fragment, prefix-confused path ve başka host'lar reddedilir. Ayrıca input SHA-256 değerini hesaplar ve deterministik JSON/Markdown makbuzu üretir.

```bash
python3 tools/x_bookmark_archive_doctor.py examples/x-bookmark-export-fictional.json \
  --json-out examples/archive-doctor-receipt.json \
  --markdown-out examples/archive-doctor-receipt.md
```

### X Bookmark Evidence Pack

Evidence Pack, geçerli bir yerel JSON export ister ve dosya tabanlı not sistemlerinde kullanılabilecek yeni bir Markdown klasörü üretir: index, bookmark başına bir not, manifest ve hash bilgileri. Çıktı yolu zaten varsa yazmayı reddeder; buna dosya, boş veya dolu klasör, symlink, repo kökü ve home klasörü dahildir. Her pack için yeni bir klasör adı seç. Çıktı isimleri güvenli ve deterministiktir. `--tag` değeri 1-64 ASCII karakter olmalı, harf veya rakamla başlamalı, devamında yalnızca harf, rakam, nokta, alt çizgi veya tire kullanmalıdır; tag'ler tekilleştirilir ve sıralanır. Obsidian ile uyumlu düz Markdown üretir; Obsidian ile bağlı, onaylı veya resmî değildir.

Repodaki `examples/evidence-pack` klasörü deterministik örnek çıktıdır; komutu oraya yazdırma. Çıktı yolu önceden var olmamalı; komutu yeniden çalıştıracaksan başka bir çalıştırma için yeni bir klasör adı seç.

```bash
OUTPUT_DIR="$(mktemp -d)/x-bookmark-evidence-pack-demo"
python3 tools/x_bookmark_evidence_pack.py examples/x-bookmark-export-fictional.json "$OUTPUT_DIR" \
  --tag fictional-fixture \
  --tag local-export
```

`examples/` ve `tests/fixtures/` içindeki örnekler hayalî veridir. Gerçek bookmark export dosyanı veya ondan üretilmiş notları public issue, demo ya da release içine ekleme.

## Büyük arşivler

Bookmark sayın yüksekse gelişmiş ayarlarda:

- bekleme süresini 2,5 saniyeye,
- yeni kayıt gelmeyince durma değerini 15 tura

çıkarabilirsin.

Önce 50 veya 100 kayıtlık bir sınırla test yapmak da yararlı olabilir.

## Sınırlamalar

Bu sürüm, sayfaya yüklenen kartları otomatik kaydırarak toplar. X toplam bookmark sayısını göstermediği için yüzde 100 eksiksizlik kanıtı sunamaz.

Aşağıdaki içerikler eksik kalabilir:

- silinmiş gönderiler,
- artık erişemediğin korumalı hesap gönderileri,
- bölgesel veya hesap bazlı olarak görüntülenemeyen içerikler,
- yavaş bağlantı nedeniyle zamanında yüklenmeyen kartlar.

X sayfa yapısını değiştirirse eklentinin DOM seçicilerinin güncellenmesi gerekebilir.

Yardımcı araçlar da export'un eksiksiz olduğunu iddia etmez; sadece extension metadata'sındaki best-effort bilgisini ve kendi doğrulama sonucunu raporlar.

## Sorun bildirirken

Public GitHub issue'suna gerçek export dosyanı ekleme. Dosyada özel bookmark verilerin bulunabilir. Chrome sürümünü, işletim sistemini, tekrar adımlarını ve mümkünse kişisel bilgi içermeyen küçük bir HTML örneğini paylaş.
