# E-kitap yazarken dikkat edilecekler

Bu kılavuz, bir koçun, danışmanın ya da içerik üreticisinin kendi e-kitabını (ya da oyun kitabını) Claude ile yazarken düşebileceği hataları önlemek için. Gerçek bir Türkçe e-kitap yazılırken çıkan dersler üzerine kurulu. Bir beceri değil, bir kontrol listesidir; yazarken yanında tut, bitirince bir daha geç.

## 1. Başlamadan: kitap kime ve ne için

- **Tek okuyucu, tek sonuç.** “Herkes için” kitap kimseye ulaşmaz. İlk cümlen şu olsun: “Bu kitabı bitiren [kim], [ne kadar sürede] [hangi somut şeyi] yapmış olur.” `icp-bulucu` kartın varsa oradan al.
- **Kitabın işi belli olsun.** Ücretsiz mıknatıs mı (okuyanı görüşmeye ya da listeye getirir), satılan ürün mü, programın ders kitabı mı? Uzunluk, ton ve sonu buna göre değişir. Mıknatıs kısa ve tek sonuçludur; ders kitabı derindir.
- **Kitap bir teklif değil, bir kanıttır.** Okuyan kitaptan sonra “bu kişi bunu gerçekten biliyor” demeli. Satış cümlesi kitabın sonunda tek yerde durur, her sayfaya serpilmez.

## 2. Yapı

- **Bir bölüm, bir sonuç.** Her bölümün başında okuyucunun bölüm sonunda elinde ne olacağını yaz. Bölüm sonunda yaptırdığın şey o sonucu üretmeli.
- **Sıra, okuyucunun sırasıyla gider, senin bilgi sıranla değil.** Ne öğrendiğin değil, okuyucunun hangi adımda takıldığı belirler.
- **Her bölümde bir uygulama.** Bir soru, bir kontrol listesi ya da bir çalışma. Okuyup geçilen bölüm unutulur.
- **Kısa tut.** Bir bölüm tek oturuşta bitmeli. Uzayan bölüm iki bölümdür.
- **Bölüm başlıkları kendi başına anlam taşısın.** İçindekiler sayfasına bakan kişi kitabın vaadini oradan okuyabilmeli.

## 3. Kanıt ve dürüstlük

- **Uydurma veri, uydurma örnek, uydurma yorum yok.** Kanıtın yoksa kanıtsız yaz; boşluğa `[kanıt: ...]` yaz ve sonra doldur. Claude'a “örnek ver” dediğinde uydurma isim ve rakam çıkarabilir; her örneğin gerçek bir kaynağı olduğunu kontrol et.
- **Gerçek örnek bir tek savı desteklesin.** Her “gerçek örnek” kutusu tek bir cümleyi kanıtlasın. Çok savı olan örnek hiçbirini kanıtlamaz. Yeni örnek aramak için yazmayı durdurma; elindeki örneği doğru yere koy.
- **Başkasının gelir rakamını yazma.** “Şu kişi ayda şu kadar kazanıyor” iddiası hem doğrulanamaz hem sana dönebilir. Bir öğretmenin kendi söylediği oranı kullanacaksan “kendi söylediğine göre” diye işaretle. Ölçtüğün sayıları kendi verinden ya da bir araçtan al.
- **Sağlık, para ve sonuç vaadi:** “garanti” yerine “çoğu öğrencim”, “bu programda ortalama” gibi dürüst ifadeler.
- **Gerçek isimler serbest, ama kaynaklı.** Bir üreticiyi örnek veriyorsan hesabının ya da videosunun bağlantısını ver. Bağlantısı olmayan isim kullanma. Kişileri birbirine karıştırma (aynı ada benzeyen iki ayrı hesap olabilir).

## 4. Alıntı, telif ve kaynak

- **Başkasının kitabından ya da videosundan metin kopyalama.** Çerçeveyi kendi kelimelerinle özetle. Bir videodan alıntı gerekiyorsa kısa tut ve videonun bağlantısını, kesitin saniyesiyle birlikte ver (“Video adı, 12:40”). Okuyan tıklayıp gerçeğine baksın.
- **Kesit kartı:** yanında video adı, süre, 1-3 satır altyazı ve tıklayınca videonun o saniyeden açıldığı bağlantı. Kesit çapalarını kitap metni değişince yeniden bağla; yoksa kart yanlış yere düşer.
- **Kaynaklar sayfası.** Okuduğun her video, makale ve kitabı, ondan ne aldığınla birlikte yaz. Sonradan “bunu nereden aldım” diye aramazsın.
- **Sorular da kaynaklı olsun.** Bir yaratıcının röportajda sorduğu soruyu kullanıyorsan hangi videodan geldiği bilinsin. Uydurma “uzmanlar şunu sorar” cümlesi yazma.

## 5. Dil ve yazım

- **Doğal Türkçe.** Yabancı dilden çevrilmiş gibi okunan cümle okuyucuyu kaybettirir. Şunlara dikkat: “Ölçülen:” gibi başlıklar, “elinde … olacak” kalıpları, art arda edilgen cümleler, virgülle uzayan zincirler. Sınama: “Bir Türk bunu böyle söyler mi?” Cümleyi sesli oku, kısa kes.
- **Açılı tırnak yok.** Okuyucu « » işaretini tırnak olarak okumaz, bozuk ok sanır. Tırnak için “ ” kullan. Adımları ok işaretiyle değil düz cümleyle yaz: “X'i aç, Y'yi seç, Z'ye bas.”
- **Bir terim, bir yazım.** “Reels” ya da “reel”, “mıknatıs” ya da “lead magnet”: birini seç, bütün kitapta aynısını kullan. Yabancı terimin Türkçesi yerleşmişse onu yaz.
- **Yer tutucuları fark edilir yap.** `[Kime]` gibi yer tutucuları kitabın içinde koyu bir renk ya da kalın yazıyla göster ki baskıya ya da yayına giderken gözden kaçmasın.
- **Listeler madde madde, sorular kart gibi.** Kod gibi görünen biçim okuyucuyu uzaklaştırır.
- **“Elini tutarak anlatıyorum” gibi cümleler yazma.** Anlat, sözünü etme.

## 6. Claude'a verdiğin komutlar (prompt) kitapta nasıl durur

- Kitaptaki her yapay zekâ komutu kapalı bir kutuda dursun: tek satır açıklama (“Yapıştır; sana sorular soracak. Dürüstçe cevapla, sonunda hazır olacak.”), bir “göster” düğmesi ve “kopyala”. Sayfayı komutlarla doldurma.
- Komutu **soru sorduran** biçimde yaz: okuyucu köşeli parantezleri doldurmasın, yapay zekâ ona soru sorsun. “Sor, uydurma, sonunda hazırı ver” iyi bir iskelettir.
- Okuyucu bir komutu kopyalayıp başka bir yapay zekâ aracına yapıştırabilsin; araca özel sözler kullanma.

## 7. Görsel ve ekran görüntüsü

- **Her ekran görüntüsünü kişisel bilgi için tara.** Kimlik numarası, telefon, e-posta, IBAN, üçüncü bir kişinin adı (sohbet başlıklarında, DM listesinde, video karelerinde). Gerçek hesaplardan alınan görüntülerde bunlar kolayca kalır.
- **Boyayla kapat, bulanıklaştırma.** Bulanık rakamlar geri okunabilir. Kapatılacak alanı kartın kendi arka plan rengiyle boya ve OCR ile tekrar tara.
- **Video kareleri de görüntüdür.** Saniyede 1 kare çıkar, hepsini tara.
- **Sosyal kanıt ekranlarında** isimler boyalı olsun; yalnız izin aldığın bir kişinin adı açık kalabilir.
- Görsel olarak az ve net: bir ekran bir fikir. Altyazı ya da etiket 6-7 kelimeyi geçmesin.

## 8. İddiaları kod ya da betikle kontrol et

Bir ürünü anlatıyorsan (bir uygulama, bir araç), kitaptaki her iddia ürünün gerçekte yaptığı şeyle uyuşmalı. İki katman:

1. **Elle:** her ekran, fiyat ve özellik cümlesini ürüne açıp bak.
2. **Betikle:** kitap bir dosya olarak üretiliyorsa küçük bir betik yaz: yasak karakterleri (« », ok işaretleri) bul, bozuk bağlantıları bul, başlık sayısını ve sayıları karşılaştır, yer tutucu kalmış mı diye tara. Bu betik her değişiklikte çalışsın. Aynı hata ikinci kez yayına çıkmaz.

## 9. Claude ile yazma düzeni

- **Önce iskelet, sonra bölüm.** Claude'a bir seferde bütün kitabı yazdırma. Önce bölüm sırasını ve her bölümün tek cümlelik sonucunu onayla.
- **Her bölümde: kaynak ver, sonra yazdır.** “Bu videoları ve notları oku, bu savı kanıtla” de. Kaynaksız “yaz” demek uydurma üretir.
- **Dil geçişini ayrı yap.** Bölümleri bitirince her dosya için ayrı bir dil turu yap; bu turda bağlantı, rakam, başlık ve kod bloklarının değişmediğini betikle doğrula.
- **Her bölümde sen oku.** Claude'un çıktısını “yayınlanabilir” saymadan önce bir okuyucu gibi oku: seni bir yerde “bu ne demek” diye durdurdu mu?
- **Büyük yeniden yazımdan sonra** kesit çapalarını, içindekileri ve bağlantıları yeniden kontrol et.

## 10. Yayın öncesi son liste

- [ ] İlk cümle: kitap kimin için, ne sonuç veriyor? Net mi?
- [ ] Her bölümde tek sonuç ve bir uygulama var mı?
- [ ] Hiçbir örnek, rakam ya da yorum uydurma değil mi? Her gerçek örneğin kaynağı ve bağlantısı var mı?
- [ ] Başkasının gelir rakamı yok mu?
- [ ] Başkasından metin kopyalanmadı mı? Alıntılar kısa ve bağlantılı mı?
- [ ] « » ve ok işaretleri kaldı mı? Terimler tutarlı mı?
- [ ] Yer tutucu (`[...]`) kalmadı mı?
- [ ] Ekran görüntüleri ve video kareleri kişisel bilgi için taranıp boyandı mı?
- [ ] Ürün anlatılıyorsa her iddia ürüne açılıp doğrulandı mı?
- [ ] Komut kutuları kapalı mı, soru sorduran biçimde mi?
- [ ] Kitabın sonunda tek, net bir sonraki adım var mı?
- [ ] Bir tanıdığına okuttun mu? “Hangi sayfada takıldın?” diye sordun mu?
