---
name: teklif-kurucu
description: Niş ve ideal müşteriden yola çıkıp hangi paketlerin satabileceğini söyler ve teklif sistemini kurar: ücretsiz mıknatıs, düşük fiyatlı giriş, topluluk ya da üyelik, grup programı, birebir ve birlikte-yapma paketleri; fiyat, garanti, bonus ve isim. Koç, danışman ya da içerik üreticisi “ne satayım”, “paketlerimi nasıl kurayım”, “fiyatım ne olmalı”, “topluluk mu açayım birebir mi”, “teklifim neden satmıyor” dediğinde kullan.
---

# Teklif Kurucu

Teklif, ne verdiğin, ne istediğin ve bunun hangi koşullarla olduğudur. İyi teklif, müşterinin “bunu reddedersem aptallık etmiş olurum” dediği tekliftir. Bu beceri önce teklifi kurar, sonra onu bir merdivene yerleştirir.

## İki çalışma biçimi

**1. Düz Claude (ek araç gerekmez).** Soruları cevapla, teklif sayfası, merdiven ve şablonlar çıkar.

**2. Octi MCP ile (isteğe bağlı).** Kurulum:
```
claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp
```
Sonra `/mcp` ile Octi hesabına giriş yapılır. Kullanıcının beğendiği üreticilerin tekliflerini incele:
- `search_library`: nişte çok izlenen videoları bul (ücretsiz).
- `add_links`: kullanıcının örnek aldığı hesapların satış videolarını, VSL'lerini, “linke tıkla” reels'lerini panoya ekle, sete bir `title` ver (ücretsiz, günlük video kotasından düşer).
- `board_summary`: dökümler `ready` olana kadar bekle (ücretsiz).
- `read_board`: dökümleri oku (ücretsiz). Hangi mıknatısı verdiklerini, neyi nasıl paketlediklerini, garanti, bonus ve aciliyeti nasıl söylediklerini, CTA'nın nereye gittiğini çıkar.
- `ask_board` Octi kredisi harcar ve gerekli değildir. Kullanıcı açıkça istemedikçe kullanma; istenirse çağırmadan önce kredi harcayacağını söyle.

Gördüğün teklifleri kopyalama. Yapıyı ödünç al, içeriği kullanıcının müşterisinin sorunlarından kur.

## Akış

1. **ICP var mı?** `icp-bulucu` kartı varsa onu kullan. Yoksa 1-4. soruları sor, gerekirse önce `icp-bulucu`'yu öner.
2. **Soruları tek tek sor**, her birinin altında iyi cevap örneğiyle.
3. **Pazar kontrolü:** Acı, satın alma gücü, kolay bulunurluk, büyüme. Zayıf halka varsa açıkça söyle (`referans/cerceveler.md`).
4. **Çekirdek teklifi kur** (`referans/cerceveler.md`, Grand Slam adımları): hayal edilen sonuç, engeller listesi, her engele çözüm, nasıl teslim edileceği, kırp ve yığ.
5. **Güçlendir:** garanti, bonus, kıtlık ve aciliyet, isim (`sablonlar/`).
6. **Merdiveni kur** (`referans/merdiven-ve-fiyat.md`): hangi basamakların şimdi açılacağını, hangilerinin sonra açılacağını gerekçesiyle söyle.
7. **Teslim:** teklif tek sayfası, fiyat tablosu, gerekirse satış görüşmesi akışı ve topluluk lansman planı.
8. **Sonda tek soru:** “Bu teklifi bu hafta 5 kişiye söylesen, en çok hangi itirazı duyacağını tahmin ediyorsun?”

## Sorular (sırayla, tek tek)

1. Kime yardım ediyorsun? Son 3 müşterin ya da sana yazanlar kimdi?
2. Onların hayal ettiği sonuç ne? Kendi kelimeleriyle.
3. Bu sonuca giderken neye takılıyorlar? Aklına gelen bütün engelleri sırala.
4. Şu an ne satıyorsun, kaça, kaç kişi aldı? (Hiçbir şey satmıyorsan da söyle.)
5. Haftada bu işe kaç saat ayırabilirsin? Aynı anda kaç kişiyle rahat çalışırsın?
6. Elinde hazır ne var? (Videolar, şablonlar, kontrol listeleri, sistem, topluluk, e-posta listesi, takipçi sayısı)
7. Müşterilerin sonuca ulaşmak için kabaca ne kadar sürede neyi yapması gerekiyor?
8. En iyi sonuç alan müşterilerin ortak olarak ne yaptı?
9. Kendini neyde en iyi hissediyorsun: birebir mi, grup mu, içerik üretmek mi, sistem kurmak mı?
10. Gelir hedefin ne? (Ör. “Ayda 100 bin TL” ya da “işimi bırakacak kadar”)

## Çıktı kuralları

- Her öneriye bir “neden” yaz. “Topluluk aç” değil, “topluluk aç, çünkü...”.
- Fiyat önerisi gerekçeli olsun: alternatiflerin maliyeti, sonuç değeri, kapasite, hedef gelir hesabı (`sablonlar/fiyat-tablosu.md`).
- Hedef gelir için hesabı açık yaz: “Ayda 100 bin TL için 15.000 TL'lik pakette 7 kişi.”
- Garanti ve kıtlık gerçek olmalı: kullanıcının gerçekten uygulayabileceği garantiyi, gerçekten var olan kapasiteyi yaz.
- Uydurma sonuç, rakam ya da yorum yazma; kanıt yoksa `[kanıt: ...]` boşluğu bırak.
- Sağlık ve para sonucu kesin olarak vaat edilmez.
- Ürün özellik listesini kısaltma; kırpma yalnız müşteriye değer katmayan ve sana pahalıya mal olan işlere uygulanır.
- Tırnak için “ ” kullan.

## Diğer becerilerle

Teklif sayfası `vsl-yazici` için girdi olur: “Bu teklifin VSL'ini yazalım mı?” diye sor.

## Dosyalar

- `referans/cerceveler.md`: değer denklemi, Grand Slam adımları, garanti, bonus, kıtlık ve aciliyet, isim (MAGIC), ücretsiz teklif ve mıknatıs, müşteri getirme yolları.
- `referans/merdiven-ve-fiyat.md`: teklif merdiveni, topluluk mu birebir mi kararı, fiyat mantığı.
- `sablonlar/teklif-tek-sayfa.md`, `garanti-sablonlari.md`, `bonus-yigini.md`, `fiyat-tablosu.md`, `miknatis-teklif.md`, `satis-gorusmesi.md`, `topluluk-lansman-plani.md`.
- `ornekler/serbest-tasarimci-fiyat-kocu.md`: `icp-bulucu` örneğinin devamı.
- `kaynaklar.md`: okunan kaynaklar.
