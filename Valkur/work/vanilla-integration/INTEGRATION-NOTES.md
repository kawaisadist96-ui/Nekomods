# Valkür vanilla animasyon entegrasyonu — 22 Ekim 2026

Test sürümü mevcut **Valkur Units Test** moduna kuruldu. Oyun içi doğrulama henüz yapılmadı.

## Yapılan işlemler

1. Kurulu oyunun Norse `unit_fp1_infantry_02_entity` tanımı incelendi. Önceki mod `mod-before/`, onarılmış Blender kaynağı `source-preserved.blend` altında korundu.
2. Bu vanilla askerin 26 animasyon klibi Valkür'ün değiştirilmiş bind iskeletine uyarlandı. Yeni hareket tasarlanmadı; vanilla hareketlerden bake alındı. Özgün kare sayıları ve kesirli FPS değerleri korundu. Çıktılar vanilla kaynaklarıyla bayt olarak aynı değildir.
3. İki idle seçeneği dahil 27 state bloğu aktarıldı: yerden kalkma, boruyla toplama, çağırma döngüsü, terhis, yürüyüş, savaşa ilerleme, kaçış, kuşatma, zafer, hastalık, hücum/savunma ve geçişler. Kapsam Norse askerin ana entity setidir. Kaynakta bağımsız yağmalama klibi yoktur.
4. Kılıç ve kalkan gövdeden ayrı ekipman meshlerine ayrıldı. Toplam 124.741 kaynak yüzün tamamı korundu: gövde 104.623, kalkan 14.877, kılıç 5.241. Hiçbir yüz silinmedi. Sırttaki kalkan ve beldeki kılıç aynı ekipmanın alternatif bağlantı kopyalarıdır.
5. El/sırt/bel bağlantıları ve vanilla zamanlı ekipman olayları eklendi. Toplanmada oyunun özgün borusu kullanılır. Terhiste kalkan sırta, silahın kaldırıldığı durumlarda kılıç bele geçer. Ayrı kın geometrisi üretilmedi.
6. Borunun yanlış yükseklikte görünmesine neden olan bağlantı dönüşümü düzeltildi. Sırttaki kalkanın dış yüzü dışarı çevrildi. Gövde export şekli ile materyal tanımı `valkurShape` olarak eşleştirildi.
7. 26 animasyon, 5 mesh ve 1 asset dosyası mevcut moda kuruldu; 32 dosyanın kurulum sonrası SHA256 değerleri doğrulandı. DDS dokular yeniden yazılmadı ve yedekle hashleri aynı. Özgün oyun dosyaları değiştirilmedi.

## Doğrulama ve sınırlar

- 26 klibin 4.348 karesindeki konum/quaternion verileri sonlu; quaternion uzunlukları geçerli. Her klibin başlangıç/orta/son karesinde Blender ile export kemik matrisleri karşılaştırıldı: en büyük mutlak fark 0,0000763.
- Beş mesh yeniden içe aktarıldı. Konum, UV, normal, üçgen ve gövde ağırlığı kontrolleri geçti. Materyal şekil adları, animasyon ID'leri, sonraki state referansları ve bağlantı kemikleri doğrulandı.
- Boru, kalkış ve terhis için Blender önizlemeleri üretildi. Bunlar oyun içi çalışma kanıtı değildir. Bütün karelerin görsel olarak kusursuz olduğu iddia edilmez.
- Mevcut modelin uç pozlardaki koltuk altı/kürk/saç deformasyonları ve ekipman ayrımında elde kalan küçük parçalar hâlâ düzeltme gerektirebilir. Boru-ağız/parmak teması ve kılıç/kalkan temasları oyun içinde özellikle kontrol edilmeli.
- LOD ve çoklu birlik performansı tamamlanmadı. Northern Lords/FP1 boru varlığı ve mevcut Norse test yönlendirmesi kullanılır.

## Düzenlenebilir dosyalar ve kanıt

- `valkur-vanilla-equipment.blend`: 26 action, gövde ve ekipman; korunmuş eski mesh gizli tutulur.
- `valkur-vanilla-preview.blend`: ayrıca vanilla boru ve önizleme sahnesi.
- `retarget.py`, `equipment.py`, `build_assets.py`: yeniden üretim adımları; ilgili kaynak blend ile çalıştırılır.
- `animation-manifest.json`, `asset-validation.json`, `integration-validation.json`, `roundtrip.json`, `equipment-report.json`: doğrulama kayıtları.
- `deployment.json`: hedef klasör, yedek ve kurulan dosyaların önce/sonra hashleri.

## Oyun testi ve geri alma

Oyunu tamamen kapatıp Valkur Units Test etkin olarak açın. Valkür'ün göründüğü Norse birlikle ordu toplama → boru/çağırma → yürüyüş → savaş → kuşatma → terhis akışını deneyin. Kalkanın sırta taşınmasını ve borunun hareket bitince kaybolmasını kontrol edin.

Geri alma için `deployment.json` içindeki `before` değeri olan dosyalar `mod-before/` kopyalarıyla geri konur; `before` değeri boş olan yeni dosyalar yalnızca kayıtlı tam hedef yollarından kaldırılır. Tüm mod klasörünü silmeyin.
