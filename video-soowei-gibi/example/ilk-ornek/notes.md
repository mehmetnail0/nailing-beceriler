# Çalışılmış örnek: video-soowei-gibi (sakin, otantik konuşma; başın arkasında büyük kelime)

Klip: aydınlık bir odada, açık renk duvarın ve kitaplı bir masanın önünde 3 dakikalık oturarak konuşma (kurgu için uydurulmuş örnek metin, gerçek bir konuşma değil). Çıktı: 1080x1920, 30 kare, 35,9 sn, 8 kesim, 35 altyazı sayfası.

## Ölçülenler (params.json, hareket.json, gramer.md)
- Kesim başına yavaş bir itiş, bez [0.36, 0.34, 0.61, 0.82]. Kesimler arası 4 karelik yumuşak geçiş.
- Altyazı Inter, cümle düzeni, yüzün altında, sayfa başına 2-4 kelime.

## Bu klip için kararlar
- Kesimler: sessizlik kenarlarından 8 kesim, tek bir hikâye anlatıyor: 4,8 milyon izlenen video, 40 kat, “acele değil sabır”.
- Başın arkasında (MODNet maskesi, choke 0,1), söylediği rakam Inter 800, yaklaşık 220 px, açık duvarda koyu mürekkep #1C1915:
  - “4.8M” (y 0,13, çünkü 0,17'de bir saç lülesi noktayı kapatıyordu);
  - “×40”, çevresine çizilen bir halka;
  - “acele”, üstü kırmızı bir çizgiyle çizilir;
  - ardından “sabır”.
- Kamera: kesim başına yavaş bir itiş (ana satırda % 5). 4 karelik geçişler.
- Altyazı: Inter 600, 54 px, `below_face: 0.025`, sayfada en çok 4 kelime / 24 karakter. Konuşma tanıma düzeltmeleri: 4.8 rakamı.
- Renk: ölçülmüş görünüm LUT'u, `--pink 0.62` ile (referans teni ısıtıyor).

## Zaman damgaları (çıktı)
- 0 açılış, yavaş itiş
- 20,8 “4.8M” başın arkasında
- 24,6 “×40”, halka 24,9'da çizilir
- 26,4 “acele”, 26,9'da çizgiyle silinir; 27,7 “sabır”

## Taşınabilirlik
Klasör boş bir dizine kopyalandı. Kurulum 7 sn, mezz yaklaşık 60 sn, yazıya dökme yaklaşık 100 sn, yüz takibi 209 sn, render tek GPU'da. Ücretli servis kullanılmaz.

## Kesim kontrolü (son miks)
`kesim_qc.py` son miksi kelime kelime yeniden yazıya döktü; 1 turda geçti, 7 kesim (soldaki cümle biter, sağdaki başlar):
- 3,67 sn  satmıyor diyenler var. | Marka gibi
- 8,50 sn  evde çektim. | Şunu bilmemiz
- 18,87 sn  yazıyor. | Ben ölçüyorum.
- 22,27 sn  izlendi. | Hesabım 9 bin
- 26,43 sn  yaptım. | acele etmiyorsun,
- 30,07 sn  uygulayabiliyorsun. | Aklına bir
- 33,90 sn  edebiliyorsun. | Yorumlara kurgu
