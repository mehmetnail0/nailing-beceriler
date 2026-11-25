---
name: icp-bulucu
description: İdeal müşteriyi (ICP) kolay sorularla bulur ve tek sayfalık müşteri kartı çıkarır. Koç, danışman ya da içerik üreticisi “kime satacağımı bilmiyorum”, “hedef kitlem kim”, “nişimi daraltmak istiyorum”, “kime konuşuyorum” dediğinde, VSL ya da teklif yazmadan önce kullan.
---

# ICP Bulucu

Kullanıcıya “kime yardım etmek istiyorsun?” diye sorma. Bu soru zordur, cevabı hayaldir. Onun yerine gerçekte olmuş şeyleri sor: konuştuğu insanlar, aldığı DM'ler, kendi yaşadığı zorluk. İnsanlar geçmişte yaptıklarını ve yaşadıkları zorluğu doğru anlatır; gelecekte ne isteyeceklerini iyi tahmin edemez. Bu becerinin bütün yöntemi bu.

## İki çalışma biçimi

**1. Düz Claude (ek araç gerekmez).** Soruları sor, cevaplardan kartı çıkar. Kullanıcı DM, yorum ya da mesaj ekran görüntüsü yapıştırırsa onları da oku; müşterinin kendi kelimeleri en değerli veridir.

**2. Octi MCP ile (isteğe bağlı).** Kurulum:
```
claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp
```
Sonra `/mcp` ile Octi hesabına giriş yapılır. Kullanıcının nişinde başarılı üreticilerin içeriklerinden ve yorumlarından kitle dili toplanır:
- `search_library`: nişte çok izlenen videoları bul (ücretsiz).
- `add_links`: kullanıcının beğendiği ya da rakip gördüğü hesapların videolarını panoya ekle, sete bir `title` ver (ücretsiz, günlük video kotasından düşer).
- `board_summary`: dökümler `ready` olana kadar bekle (ücretsiz).
- `read_board`: dökümleri oku (ücretsiz). Kitlenin hangi acıyı hangi kelimelerle anlattığını, hangi kancaların tuttuğunu, hangi teklife yönlendirildiğini not et.
- `ask_board` Octi kredisi harcar ve gerekli değildir. Kullanıcı açıkça istemedikçe kullanma; istenirse çağırmadan önce kredi harcayacağını söyle.

Bulduğun kalıpları kopyalama; kartı kullanıcının kendi cevaplarıyla kur, dışarıdan gelen kelimeleri “kitlede duyulan” diye ayrı işaretle.

## Kullanıcı zaten çok yazdıysa (atlama yok)

İlk mesajında kim olduğunu, uzmanlığını, hatta hedef kitleyi anlatan biri de olur (“ben X alanında uzmanım, şunları yaptım, nasıl bir marka kurayım?”). Bu, ICP'nin bittiği anlamına gelmez; çoğu zaman uzmanlığı anlatır, müşteriyi anlatmaz. Şöyle yap:

1. Yazdıklarını üç sütunda ayır: **bilinen** (kullanıcının söylediği), **tahmin** (senin çıkarımın), **eksik** (kimin için, neden şimdi, ne ödüyor, nerede bulunur).
2. Üç satırlık özet ver ve “Doğru mu?” diye sor.
3. Yalnız **eksik** kalanları, tek tek sor. Cevaplanmış soruyu tekrar sorma, ama kart, aç kalabalık testi ve doğrulama planı yine yapılır.
4. Uzun brief'i ya da “derin araştır” isteğini bahane edip soruları geçip doğrudan plan yazma. Araştırma sorunun yerine geçmez; kullanıcının kendi müşteri bilgisi (kim yazdı, kim ödedi) webden bulunamaz.
5. Webden bulduğun pazar bilgisinin yanına kaynağı ya da `[doğrula]` yaz. Fiyat ve yasa iddiasını kanıtsız kesin söyleme.

## Şirkete satış (B2B) ve uzmanlık işleri

Alıcı bir şirketse (savunma, sağlık, hukuk, üretim, medya...) kart bir kişiyi değil bir alım ekibini anlatır. Karta şunları ekle:

- **Kullanan, savunan, bütçe sahibi, karar veren, engelleyen:** kim kim? Çoğu zaman beşi ayrı kişidir.
- **Alım tetikleyicisi:** fuar, ihale, ihracat hedefi, denetim, yeni dönem bütçesi. “Ne zaman ihtiyaç duyar” sorusu “kim” sorusundan önce gelir.
- **Şu an kime ödüyorlar:** ajans, danışman, iç ekip, hiç kimse. Yerine geçeceğin şey bu.
- **Satın alma yolu:** doğrudan mı, tedarikçi ya da ajans üzerinden mi? Büyük alıcıya ilk adımda ulaşılamıyorsa onlara satış yapan küçük tedarikçiler ayrı bir kitle olarak kartlanır.
- **Kullanıcının kısıtları:** işvereni var mı, yazılı izin gerekir mi, para ödeyen firma hakkında içerik üretince çıkar çatışması doğar mı. Bunu en başta sor; çözüm planın parçası olur.
- **Kanıt:** vaka çalışması ya da referansı yoksa “ilk 3 müşteri” için indirimli ama izinli vaka çalışması planı yaz.

Alıcı bireyse bu bölümü atla.

## Sohbet penceresinde (dosya ve MCP yok)

Bu beceri claude.ai gibi bir sohbet penceresinde GitHub bağlantısından okunuyor olabilir. Alt dosyalar (`sablonlar/`, `referans/`) açılamazsa durma; soruları ve aşağıdaki asgari kartı SKILL.md'den kullan:

> **Kart (asgari):** Kim (durum, tetikleyici) · Derdi (kendi kelimeleriyle, tırnakta) · İstediği · Önce ne denedi · İtirazı · Nerede bulunur · Bilinen / Tahmin etiketi.
> **Aç kalabalık testi:** acısı büyük mü, ödeyecek parası var mı, kolay bulunur mu, büyüyor mu (her biri 1-5 ve tek cümle).
> **Doğrulama:** 5-10 kişiye tek soruluk DM.

Çıktıyı sohbette ver; dosya yazamıyorsan düzenlenebilir bir taslak belgeye koy.

## Akış

1. **Soruları tek tek sor.** Her sorunun altına kısa bir iyi cevap örneği koy (`sablonlar/soru-bankasi.md`). Kullanıcı “bilmiyorum” derse bir sonraki soruya geç, sonra dön. Kullanıcı zaten anlattığı bir soruyu atlamak istersen yukarıdaki “atlama yok” bölümüne göre yap.
2. **Ara özet.** 6. sorudan sonra duyduklarını 3 satırda söyle: “Şu ana kadar duyduğum kişi şu. Doğru mu?”
3. **Kartı yaz** (`sablonlar/icp-karti.md`).
4. **Aç kalabalık testi** (`sablonlar/ac-kalabalik-testi.md`): dört ölçüt, her biri 1-5 puan ve tek cümle gerekçe.
5. **Konumlandırma** (`sablonlar/konumlandirma.md`): neyin yerine seçiliyor, neyi farklı, kime en çok uyuyor.
6. **Doğrulama planı** (`sablonlar/dm-ve-anket.md`): kartı tahmin olmaktan çıkarmak için 5-10 kişiye sorulacak DM ve tek soruluk anket.
7. **Sonda tek soru sor:** “Bu karttaki kişiyi gerçek hayatta tanıyor musun? Adını içinden söyleyebiliyorsan doğru yoldayız.”

## Sorular (sırayla, tek tek)

1. Bugüne kadar sana para ödeyen ya da ücretsiz yardım ettiğin en iyi 3 kişiyi düşün. Ne iş yapıyorlardı, hayatlarının hangi dönemindeydiler?
2. Bu kişilerden biri sana ilk yazdığında tam olarak ne demişti? Hatırladığın kadarıyla aynen yaz.
3. Sana en sık gelen DM ya da yorum sorusu ne? (Ekran görüntüsü yapıştırabilirsin.)
4. Bu konuda senin kendi yaşadığın en zor dönem neydi? O zaman ne denedin, ne işe yaramadı?
5. Sana gelenler senden önce neleri denemişti? (Kurs, uygulama, başka koç, YouTube, hiçbir şey...)
6. Sana tam o hafta yazmalarına ne sebep olmuştu? Bir olay, bir rakam, bir kriz?
7. Çalışmaktan en çok keyif aldığın kişi kimdi, en çok yorulduğun kişi kimdi? İkisini ayıran ne?
8. Bu kişiler parayı nereden kazanıyor, bu sorun için kabaca ne harcamaya alışkınlar?
9. Bu kişiler gün içinde nerede vakit geçiriyor? Hangi hesapları takip ediyor, hangi gruplarda?
10. Satın almadan önce en sık hangi itirazı duydun? (“Pahalı”, “vaktim yok”, “eşime sorayım”...)
11. Seninle çalıştıktan sonra en çok neye sevindiler? Kendi kelimeleriyle.

Kullanıcı hiç müşteri görmemişse 1, 2, 6 ve 11 yerine kendi geçmiş haline dair sor (“o dönemde biri sana ne söyleseydi para öderdin?”) ve doğrulama planını zorunlu yap.

## Çıktı kuralları

- Acıları ve istekleri müşterinin kendi kelimeleriyle yaz, tırnak içinde. Senin yorumun ayrı satırda.
- Demografi (yaş, şehir) en sona; asıl kart durum, tetikleyici ve denenenler.
- Tahmin ile veriyi ayır: kullanıcının söylediği “bilinen”, senin çıkarımın “tahmin” etiketi alır.
- Birden fazla kitle çıkarsa her biri için kısa kart yaz, sonra hangisinin aç kalabalık testinde önde olduğunu söyle. Seçim kullanıcının.
- Gerçek kişi adı, telefon ya da kimliği belli eden bilgi karta yazılmaz.
- Tırnak için “ ” kullan.

## Diğer becerilerle

Kart `teklif-kurucu` ve `vsl-yazici` için girdi olur. Kullanıcı kartı onaylarsa “Bu kartla teklifini kurmak ister misin?” diye sor.

## Dosyalar

- `referans/cerceveler.md`: Ask Method, Jobs-to-be-done, aç kalabalık, Dunford konumlandırması; ne zaman hangisi.
- `sablonlar/soru-bankasi.md`: soruların iyi ve zayıf cevap örnekleri, takip soruları.
- `sablonlar/icp-karti.md`: boş kart.
- `sablonlar/ac-kalabalik-testi.md`: puanlama tablosu.
- `sablonlar/konumlandirma.md`: alternatifler, farklar, değer temaları.
- `sablonlar/dm-ve-anket.md`: doğrulama DM'leri ve tek soruluk anket.
- `ornekler/serbest-tasarimci-fiyat-kocu.md`: baştan sona bir örnek.
- `kaynaklar.md`: okunan kaynaklar.
