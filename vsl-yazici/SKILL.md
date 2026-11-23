---
name: vsl-yazici
description: Koç, eğitmen ya da içerik üreticisi için çekime hazır VSL (video satış mektubu) metni yazar. Birkaç kolay soru sorar, sonra kısa (2-5 dk) ve uzun (15-20 dk) metni çekim notları, ekran yazıları ve harekete geçirme çağrısıyla birlikte çıkarır. “VSL yaz”, “satış videosu metni”, “tanıtım videosu senaryosu”, “webinar metni”, “satış sayfası videosu” denince kullan.
---

# VSL Yazıcı

Amaç: kullanıcı bu konuşmadan çıkınca elinde okuyup çekebileceği bir metin olsun. Metin, kendi sesine ve kendi müşterisinin cümlelerine yaslansın; şablon iskelettir, kalıp değildir.

## İki çalışma biçimi

**1. Düz Claude (araç gerekmez).** Soruları sor, cevapları al, metni yaz. Başka hiçbir şey kurmaya gerek yok.

**2. Octi MCP ile (isteğe bağlı).** Kullanıcı beğendiği üreticilerin VSL'lerinden, reels'larından öğrenmek isterse:

```
claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp
```

Sonra `/mcp` ile Octi hesabına giriş yapılır. Akış:
- `search_library` (ücretsiz): nişte işe yaramış videoları bul, ya da kullanıcının verdiği linkleri kullan.
- `add_links` (ücretsiz, günlük video kotasından düşer): seçilen linkleri bir panoya ekle, sete bir `title` ver.
- `board_summary` (ücretsiz): metin dökümleri `ready` olana kadar bekle.
- `read_board` (ücretsiz): dökümleri oku. Açılış cümlelerini, büyük fikri, sorunun nasıl adlandırıldığını, teklifin nasıl sunulduğunu ve kapanışı not et. Cümle kopyalama; yapıyı ödünç al.
- `ask_board` **Octi kredisi harcar** ve isteğe bağlıdır. Yalnızca kullanıcı Octi'nin kendi sohbetinde cevap isterse ya da cevabın panoda kalmasını isterse kullan; çağırmadan önce kredi harcayacağını söyle. Varsayılan: dökümleri sen okur, metni sen yazarsın.

Okuduğun referanslardan çıkardığın kalıpları (kanca tipi, hikâye uzunluğu, teklif sunumu) metne uygula ve kullanıcıya hangi referanstan neyi aldığını bir satırla söyle.

## Akış

1. **Soruları tek tek sor.** Her soruda iyi bir cevap örneği ver. Kullanıcı “bilmiyorum” derse bir sonraki soruya geç, sonra o boşluğu kendi önerinle doldurup onaya sun.
2. **Kısa özet ver** (5-6 satır): kime, hangi sonuç, büyük fikir, sorunun adı, çözümün adı, teklif ve fiyat. “Doğru mu?” diye sor. Burada düzeltme ucuzdur.
3. **Metni yaz.** Önce kısa, sonra uzun sürüm. Biçim: `sablonlar/cekim-plani.md`.
4. **Kontrol listesi** (aşağıda) ile metni kendin gözden geçir, sonra teslim et.
5. Teslimden sonra tek soru: “Hangi bölüm sana yabancı geldi?” Oradan düzelt.

## Sorular (tek tek, sırayla)

Her soruyu sorarken altına bir örnek cevap ekle. Örnekler `sablonlar/soru-ornekleri.md` dosyasında.

1. Ne satıyorsun? Bir cümleyle, ne olduğunu ve ne kadar sürdüğünü anlat.
2. Bunu alan biri ne zaman, nasıl bir sonuç görüyor? Gerçek bir öğrencinden ya da müşterinden bir örnek ver.
3. Sana en son yazan ya da seninle konuşan müşteri adayı tam olarak ne demişti? Kendi kelimeleriyle yaz.
4. Bu insanlar daha önce neyi denedi de olmadı?
5. Sence neden olmadı? Herkesin gözden kaçırdığı tek şey ne?
6. Senin yolunu farklı yapan şey ne? Adı var mı, yoksa birlikte koyalım mı?
7. Bu işe nasıl başladın? En zor anın neydi, neyi fark ettin?
8. Elinde hangi kanıt var: rakam, ekran görüntüsü, yorum, önce-sonra? (Yoksa yok de; uydurmayacağız.)
9. Fiyat ne, ödeme nasıl? Garanti ya da iade var mı?
10. Video izlendikten sonra izleyici tam olarak neye basacak? (Form, WhatsApp, ödeme sayfası, görüşme takvimi)
11. Kameraya sen mi konuşacaksın, yoksa ekran yazısı ve dış ses mi? Ne kadar süre çekebilirsin?

Kullanıcı `icp-bulucu` ya da `teklif-kurucu` çıktısı verdiyse oradaki cevapları kullan, aynı soruyu tekrar sorma.

## Metnin omurgası

Ayrıntı `referans/cerceveler.md` içinde. Kısaca:

- **Tek büyük fikir.** İzleyicinin inanması gereken tek şey. Birden fazla şeye ikna etmeye çalışan video zayıflar.
- **Sorunun adı ve çözümün adı.** İzleyici neden şimdiye kadar başaramadı (sorunun mekanizması) ve neden bu sefer olacak (çözümün mekanizması). İkisi mantıkla birbirine bağlı olmalı.
- **Suç onda değil.** Başarısızlığı izleyicinin üstünden al; ama sorumluluğu ona geri ver.
- **Hikâye kısa ve dürüst.** Önce, kırılma anı, fark ediş, sistem.
- **Teklif geç gelir.** Satış kısmına gelmeden önce izleyici bir şey öğrenmiş olmalı.
- **Değer yığını, sonra fiyat.** Her parçanın neden değerli olduğunu gerekçesiyle söyle; havadan rakam atma.
- **Garanti olumlu cümleyle.** Önce ne yaşayacağını söyle, iade cümlesi en sonda.
- **CTA açık, zekice değil.** Tam olarak ne yapacak, neden şimdi.

## Çıktı biçimi

Her bölüm için tablo ya da blok:
- **Süre** (yaklaşık saniye)
- **Söylenen** (konuşma metni, kısa cümleler, konuşma dili)
- **Ekranda yazı** (en fazla 6-7 kelime)
- **Çekim notu** (çekim ölçeği, yer, B-roll, jest)

Kısa sürüm 300-700 kelime, uzun sürüm 2000-2800 kelime civarı (Türkçe konuşma hızıyla dakikada ~130 kelime). Sonunda: önerilen 3 başlık/kapak yazısı, 3 alternatif açılış, sayfa altı için CTA metni.

## Kontrol listesi (teslimden önce)

- Tek büyük fikir var mı, metnin her bölümü ona hizmet ediyor mu?
- İlk 10 saniyede kime konuştuğu ve ne kazanacağı belli mi?
- Kullanıcının müşterisinin kendi cümlelerinden en az iki tane metinde geçiyor mu?
- Uydurma rakam, uydurma yorum, uydurma “bilimsel” iddia yok. Kanıt yoksa kanıtsız yaz; boşluğa `[kanıt: ...]` notu koy.
- Sağlık, para, kilo gibi alanlarda kesin sonuç vaadi yok; “çoğu öğrencim”, “bu programda ortalama” gibi dürüst ifadeler.
- CTA bir tane ve net.
- Cümleler sesli okunabilir mi? Uzun cümleyi böl.
- Metinde açılı tırnak ve ok işareti yok; tırnak “ ” ile.

## Dosyalar

- `referans/cerceveler.md`: Benson, Brunson, Hormozi, Georgi, AIDA/PAS ve bunların VSL'de nereye oturduğu.
- `sablonlar/kisa-vsl.md`, `sablonlar/uzun-vsl.md`: doldurulabilir iskeletler.
- `sablonlar/acilis-kancalari.md`: açılış tipleri.
- `sablonlar/kapanis-ve-cta.md`: kapanış tipleri, garanti cümleleri, CTA.
- `sablonlar/cekim-plani.md`: teslim biçimi.
- `sablonlar/soru-ornekleri.md`: her soru için iyi cevap örnekleri.
- `ornekler/fitness-kocu.md`, `ornekler/icerik-koclugu.md`: uydurma nişlerde tam örnekler.
- `kaynaklar.md`: okunan kaynaklar.
