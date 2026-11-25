# Nailing becerileri

İçerik üreticileri, koçlar ve tek kişilik işler için Claude Code becerileri. Hepsi seni sorularla yürütür, sonunda elinde kullanılır bir dosya kalır. Hiçbiri senin yerine bir şey yollamaz ya da yayınlamaz.

![Kısa anlatım: videonu çek, beceriyi söyle, hazır reels al](gorseller/kisa-anlatim.svg)

## Sekiz beceri

| Beceri | Ne yapar | Claude'a ne dersin |
|---|---|---|
| `icp-bulucu` | Kolay sorularla kime konuştuğunu çıkarır: derdi kendi kelimeleriyle, istediği, itirazları, nerede takıldığı. | “ICP’mi bul” |
| `teklif-kurucu` | Nişine göre hangi paketi satabileceğini söyler, teklif merdivenini kurar: ücretsiz mıknatıs, düşük fiyat, topluluk, grup, birebir yüksek fiyat. Şablonlarıyla. | “Teklifimi kur” |
| `vsl-yazici` | Birkaç soruyla çekime hazır satış videosu metni yazar: kısa ve uzun hali, çekim notu, ekran yazısı, çağrı. | “VSL yaz” |
| `video-sinematik-sade` | Kendi dikey konuşma klibini sakin, sinematik bir reele çevirir. | “Sinematik sade kurgu yap” |
| `video-kafa-arkasi-yazi` | Kafanın arkasından akan büyük yazı ve grafikle konuşma reeli. | “Kafa arkası yazılı kurgu yap” |
| `video-soowei-gibi` | “SooWei gibi”: sakin, otantik anlatım; küçük harfli altyazı, ara görüntülerle gidiş geliş. | “Videomu SooWei gibi kurgula” |
| `video-kallaway-gibi` | “Kallaway gibi”: üstte siyah panelde başlık ve çizim, altta sen, kelime kelime altyazı. | “Videomu Kallaway gibi kurgula” |
| `video-mino-gibi` | “Mino gibi”: POV başlığı, küçük altyazı, sürekli yavaş zoom, doygun renk. | “Videomu Mino gibi kurgula” |

Sıra önerisi: önce `icp-bulucu`, sonra `teklif-kurucu`, sonra `vsl-yazici`. Her biri bir öncekinin dosyasını okur, yoksa sorar.

Bir şey yazarak başlasan da olur (“ben şu alanda uzmanım, nasıl bir teklif kurayım?”). Beceriler yazdıklarını “bilinen / tahmin / eksik” diye ayırır, yalnız eksik soruları sorar; sırf yazdın diye adımları atlamaz. Şirkete satış (B2B), işvereni olan uzmanlar ve kendi VSL'ini yapıştıranlar için ayrı bölümleri var.

## Kılavuzlar

| Kılavuz | Ne için |
|---|---|
| [`kilavuzlar/e-kitap-yazarken.md`](kilavuzlar/e-kitap-yazarken.md) | E-kitap yazarken dikkat edilecekler: yapı, kanıt, alıntı ve telif, Türkçe yazım, komut kutuları, ekran görüntüsünde kişisel bilgi, yayın öncesi liste. |

## Kurulum

```bash
git clone https://github.com/mehmetnail0/nailing-beceriler ~/nailing-beceriler
mkdir -p ~/.claude/skills
cp -R ~/nailing-beceriler/*-* ~/.claude/skills/
```

Sonra Claude Code'u aç ve tablodaki cümlelerden birini yaz. Video becerileri ilk çalışmada kendi kurulum kontrolünü yapar (ffmpeg, python paketleri, kişi kesme modeli); ne eksikse söyler.

## İki şekilde çalışır

**Düz Claude ile.** Hiçbir bağlantı gerekmez. Soruları cevaplarsın, çıktı gelir.

**Octi ile, daha iyi.** Sevdiğin içerik üreticilerinin videolarını önce okutursan yazı ve kurgu onların yapısından beslenir:

```bash
claude mcp add --transport http --scope user octi https://app.getocti.si/api/mcp
```

Sonra `/mcp` ile giriş yap. Kütüphane araması, link ekleme ve tahtayı okuma ücretsizdir. Octi'nin kendi sohbetine sordurmak (`ask_board`) kredi harcar ve isteğe bağlıdır.

## Kaynaklar

Her iş becerisinin klasöründe `kaynaklar.md` var; her video becerisinin `reference/kaynaklar.md` dosyası hangi yaratıcının hangi reellerinden (bağlantı, izlenme sayısı, okunma tarihi) neyin alındığını yazar. Başkasının videosu pakette yok, yalnız bağlantı ve bizim ölçtüğümüz sayılar var. Her iş becerisinin klasöründeki `kaynaklar.md`: okunan her video ve yazının linki, ondan ne alındığı. Çerçeveler kendi kelimelerimizle özetlendi, kitaplardan metin kopyalanmadı.

Video becerilerinin kişi kesme modeli (RVM, GPL-3.0) pakette yok; kurulum kontrolü lisansını ve adresini yazıp indirir.
