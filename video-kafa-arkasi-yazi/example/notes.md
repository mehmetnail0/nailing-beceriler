# Çalışılmış örnek: video-kafa-arkasi-yazi (başın arkasında akan doküman)

Klip: loş bir odada, siyah tişörtlü bir içerik üreticisinin 2,5 dakikalık konuşması (kurgu için uydurulmuş örnek metin, gerçek bir konuşma değil). Çıktı: 1080x1920, 30 kare, 38,3 saniye, 12 kesim, 46 altyazı sayfası.

## Ölçülenler (referans kartı ve hareket.json'dan, tahmin yok)
- Doküman satırı = 0,068 H. Her bölümden 0,2 sn önce başlayan, 0,7 sn süren, expo-out bir kaydırma. Kaydırmalar arasında saniyede 0,8 % H sürüklenme.
- Harfler: 0,02 sn aralıkla girer, 0,2 sn solar, 0,015 H yükselir. Neon çubuk: 0,012 H yüksekliğinde, satırın 0,022 H altında, 0,1 sn'de açılır, opaklık 0,9. Renk sırası: sarı, turuncu, limon yeşili, mercan, mor.
- El yazısı satırlar 0,5 sn'de yazılır. CTA oku 0,5 sn'de çizilir.
- Kamera: açılışta -25,6 % (0,667 sn, bez [0.219, 0.779, 0.495, 0.66]); tipik hareket bez [0.468, 0.741, 0.495, 0.777]; bir tane +10,2 % itiş.
- Altyazı: sayfa başına 1-3 kelime, merkez 0,58, boy 0,024 H.

## Bu klip için kararlar
- Kesimler: en güçlü 12 cümle, sessizlik kenarlarından kesildi (konuşma tanıma ilk kelimeyi duraklamanın içine doğru geri çeker, bu yüzden kelimenin bitişi kenardır). Sıra: önce rakamlar (8.000 abone, 120.000 izlenme), sonra iki el yazısı satır, altı adım, özet ve CTA.
- Bölümler: her cümle bir bölüm. Rakamlar Inter 800, 74 px. Adımlar “1. … 6.” başlıkları, 60 px; her birinde söylenen anahtar kelimede açılan bir çubuk. El yazısı satırlar Instrument Serif Italic, #E7C955.
- Oda: bgplate dim 0,42, sat 0,45. Duvar açık renk ve açık duvarda neon okunmuyor. 384 px'de kesim duvara taştığı için MODNet maskesi choke 0,1 ile çalışıyor.
- Altyazılar çenenin altına oturtuldu (`below_face: 0.02`): referansın 0,58 yeri bu konuşmacıda çeneye denk düşüyordu.
- Kamera: 1,256'dan 1,0'a açılış, dönüşümlü % 3 hareketler, “Formülü al, kopyalama” satırında % 10,2 itiş.

## Zaman damgaları (çıktı)
- 0,0 “8.000 abone” ve açılış geri çekilmesi; 1,1 “120.000 izlenme”
- 4,0 ve 5,7 iki el yazısı satır yazılır
- 9,7, 14,6, 17,6, 22,3, 24,6, 29,5 adım 1-6, her birinde anahtar kelimede çubuk, adım başına bir kaydırma (5. adımda % 10,2 itiş)
- 33,1 özet: altı adım 40 px'de, sırayla geri gelir
- 35,2 CTA “yorumlara: kurgu”, sarı çubuk 36,7, ok 37,3

## Taşınabilirlik
Klasör boş bir dizine kopyalandı, `python3 scripts/setup_check.py` 7 sn'de tamam dedi. mezz 61 sn, yazıya dökme 115 sn, yüz takibi 201 sn, render tek GPU'da yaklaşık 2-3 dk (CPU yolu da çalışır, yalnız daha yavaş). Ücretli servis ya da özel depo kullanılmaz.

## Kesim kontrolü (son miks)
`kesim_qc.py` son miksi kelime kelime yeniden yazıya döktü; 12 kesimde 2 turda geçti. Kesim noktaları (soldaki cümle biter, sağdaki başlar):
- 3,97 sn  izlenme aldı. | Saatlerce yoğurup
- 5,67 sn  durmadan, | sabah uyanıp
- 9,67 sn  şunu yapardım. | Önce yeni
- 14,60 sn  yazı olabilir. | Kendi damak
- 17,57 sn  birleşimi. | Formatı videoyu
- 22,30 sn  bakarım. | O formatı
- 24,97 sn  bulurum. | Sonra o
- 29,93 sn  taklit etmiyorum. | İlk yoğurduğum
- 31,73 sn  yazıyorum. | Sonra tüm
- 33,50 sn  yazıyorum. | Tutan tarifi
- 34,03 sn  Tutan tarifi | yapabiliyorsun.
- 34,73 sn  yapabiliyorsun. | Bunu
- İlk teslim edilen sürümde kapı 5 hata buldu: bir kelimenin kesimle yarım kalması, bir kesimin kelimenin içine düşmesi, iki yetim kelime ve bir kekeleme gibi okunan tekrar.
- Düzeltme: yetim kelimenin kenarı kaydırıldı; tekrarda “yavaş…” parçası düşürüldü, kenar sonraki kelimeden önceki duraklamaya alındı. Bir “yavaş”ı tutan sürüm yalnız 140 ms olarak, yarım bir parça gibi okunduğu için yayınlanmadı.
- Yalnız uyarı (kelime tam okundu): 5,67 sn word_edge, 29,93 sn tight_joint.
