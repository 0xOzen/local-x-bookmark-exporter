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

1. [Son GitHub sürümünü](https://github.com/0xOzen/local-x-bookmark-exporter/releases/latest) aç, `local-x-bookmark-exporter-v<version>.zip` dosyasını indir ve ZIP'i çıkar. Alternatif olarak GitHub sayfasında **Code > Download ZIP** seçeneğini kullanabilir veya repoyu Git ile klonlayabilirsin:

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

## Sorun bildirirken

Public GitHub issue'suna gerçek export dosyanı ekleme. Dosyada özel bookmark verilerin bulunabilir. Chrome sürümünü, işletim sistemini, tekrar adımlarını ve mümkünse kişisel bilgi içermeyen küçük bir HTML örneğini paylaş.
