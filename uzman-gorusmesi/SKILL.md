---
name: uzman-gorusmesi
description: Bir uzmanla (mentör, koç, danışman, usta) ilk görüşmeyi 45-60 dakikada yürütür ve onun gerçek cevaplarından teklifin ham maddesini toplar. “Mağaza kurarım”, “reklam yönetirim”, “koçluk veririm” gibi hizmet tanımını “kime, hangi sonuç, ne sürede” sorularıyla teklife çevirmek için kullan. Kullanıcı “uzmanla görüşeceğim”, “mentörün öğrencilerine ne soracağım”, “ilk görüşme soruları”, “müşterimin teklifini onunla çıkaracağım”, “görüşme notlarını teklife çevir” dediğinde çalışır. Hem Claude'un soruyu sorduğu canlı biçimi hem kağıt kalemle yazdırılabilir soru sayfası var.
---

# Uzman Görüşmesi

Teklifi sen uydurmazsın; uzmanın geçmiş öğrencilerinde ve müşterilerinde zaten var. Bu beceri o cevapları çıkaran sorulardır: kime, hangi sonuç, ne sürede, nasıl, neden o. Hepsi geçmişte olmuş şeyleri sorar, hayali sormaz.

Çıktı: tek bir `gorusme-notlari.md`. Sonra `icp-bulucu` → `teklif-kurucu` → `vsl-yazici` bu dosyayı okuyarak çalışır; yoksa baştan sorarlar.

## İki biçim, birini seç

**Canlı (Claude sorar).** Uzman ya da görüşmeyi yürüten kişi Claude'un karşısında. Claude soruları sırayla, birer birer sorar, cevabı aynen yazar.

**Kağıt kalem.** `sablonlar/kagit-sayfa.md` dosyasını yazdır; görüşmede el yazısıyla doldur, sonra fotoğrafını ya da yazısını Claude'a ver. Claude “bilinen / tahmin / eksik” ayırır ve eksik kalanı sorar.

Kullanıcı hangisini istediğini söylemediyse tek soruyla sor.

## Başlamadan

1. Görüşme kaç dakika? Varsayılan 45-60. Süreyi aşağıdaki bölümlere böl, sırayı bozma.
2. Uzmanın görüşmeyi kaydetmeye izni var mı? Kayıt izinsiz yapılmaz. İzin yoksa notla ilerle.
3. Uzmanın bu sorulara cevap verirken mağaza, gelir ya da öğrenci rakamlarını paylaşma zorunluluğu olmadığını baştan söyle. Paylaşırsa kanıtıyla yazılır, paylaşmazsa boş kalır.

## Nasıl sorarsın

- **Birer soru, uzmanın kelimeleriyle.** Cevabı kendi cümlenle değiştirme; aynen yaz. Uzmanın kelimeleri VSL'in ham maddesidir.
- **Geçmişi sor.** “Son üç öğrencin kimdi?” iyidir. “İdeal öğrencin kim olsun?” hayaldir; sorma.
- **Belirsiz cevabı bir kez derinleştir.** “Yeni başlayanlar” denirse: “En son bu tür kim yazdı? Ne yazdı?” Rakam, isim (izinliyse), tarih iste. İkinci kez de belirsizse `[eksik]` yaz ve geç.
- **Kanıt yuvası.** Her sonuç iddiasının yanına `[kanıt: ?]` koy: ekran görüntüsü, öğrencinin izni, mağaza bağlantısı. Kanıt yoksa iddia “uzmanın beyanı” diye işaretlenir.
- **Uydurma yok.** Uzmanın söylemediği hiçbir rakamı, sonucu ya da öğrenci hikâyesini ekleme. Boşluk boş kalır.
- **Söz sınırı.** Ne uzmana ne öğrencilerine gelir ya da satış sözü yazılır. Vaat yalnız ne teslim edilir ve hangi süreçle olduğudur.
- **Fiyat uzmana ait.** Fiyat kararını önermeden önce uzmanın bugünkü fiyatını, kaç kişi aldığını, ödeme biçimini sor.

## Görüşmenin akışı (60 dakika; 45'te her bölümü ~%25 kısalt)

| Bölüm | Dakika | Ne | Sorular (soru-bankasi.md) |
|---|---|---|---|
| A. Açılış | 5 | Neden görüşüyoruz, kayıt izni, “kimseye satış yapmıyoruz, anlamaya çalışıyoruz” | — |
| B. Kime | 12 | Son öğrenciler, ilk mesajları, kimle çalışmak istemez | 1, 2, 6 |
| C. Sonuç ve süre | 15 | En iyi sonuç, öncesi sonrası, ne kadar sürdü, nerede takılıyorlar | 3, 4, 5 |
| D. Neden o | 10 | Neden onu seçtiler, satın almayanlar neden almadı, itirazlar | 7, 10 |
| E. İş ve kapasite | 8 | Fiyat, kaç kişi aldı, ödeme, haftada kaç saat, aynı anda kaç kişi | 8, 9 |
| F. Kapanış | 10 | Kanıt iste, geri okumayı yap, sonraki adımı belirle | aşağıda |

Süre aşılırsa D ve E sıkıştırılır, B ve C sıkıştırılmaz: kime ve hangi sonuç, teklifin omurgasıdır.

## Kapanış (F)

1. **Geri oku:** “Seni şöyle anladım: ___ kişilerle çalışıyorsun, ___ sonucuna ___ sürede götürüyorsun, bunu ___ yoluyla yapıyorsun. Doğru mu?” Düzeltmeyi aynen yaz.
2. **Teklif testi (cümleyi tamamlat):** “___ (kim) için, ___ (süre) içinde, ___ (sonuç), ___ (yol) ile.” Dört boşluktan biri boşsa teklif henüz hizmet tanımıdır. Söyle ve hangi soruya geri dönüleceğini yaz.
3. **Kanıt iste:** üç öğrencinin cevabına ulaşmak için izin, 1-2 DM ya da yorum ekran görüntüsü, bir öncesi/sonrası. İsimleri sonra boyarız.
4. **Sonraki adım:** hangi öğrencilerle ne zaman konuşulur (bkz. `referans/ogrenci-gorusmesi.md`), VSL çekimi için kim ne getirir.

## Çıktı: `gorusme-notlari.md`

```
# <uzmanın adı / işi> · görüşme notları · <tarih>
## Cevaplar (aynen)   → soru no, cevap, [kanıt: ...]
## Bilinen / Tahmin / Eksik
## Teklif cümlesi      → dört boşluk, hangisi dolu
## İtirazlar ve takıldıkları yerler (VSL hammaddesi)
## Uzmanın kendi cümleleri (alıntı)
## Eksik kalan 2-3 soru → ikinci mesajda sorulacak
## Sonraki adım
```

Sonra: `icp-bulucu`, `teklif-kurucu`, `vsl-yazici` sırasıyla.

## Zaten çok anlatılmışsa

Uzmanın ya da kullanıcının önceden yazdıklarını üç sütuna ayır (bilinen / tahmin / eksik), özeti ver, “Doğru mu?” diye sor, yalnız eksik soruları sor. Cevaplanmış soruyu tekrar sorma; ama kanıt ve teklif testi yine yapılır.

## Kaynaklar

`kaynaklar.md`
