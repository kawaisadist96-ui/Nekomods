# Valkür — Cursor için devir ve uygulama isteği

## Hedef
Bu paketteki Valkür karakterini onar ve kullanıcının CK3 moduna entegre et. Mevcut rig başarısız bir inceleme prototipidir; oyuna hazır teslim değildir. Kaynakları koru, değişiklikleri ayrı çalışma ve export kopyalarında yap. Kurulu oyunun sürümünü, hedef modu ve kullanılan model/animasyon araçlarını yerelde doğrula. Belirsiz bir hedef mod varsa dosya yazmadan kullanıcıdan hedefi öğren.

## Paketi nasıl açmalısın?
Önce rapor.html ve bu notu oku; sonra valkur-rig-review.blend dosyasını Blender'da aç. Raporun renders/, reports/ ve source/ bağlantıları pakette korunmuştur. Bu paket yerelde bulunan dosyalardan hazırlanmıştır; önceki sohbetin /mnt/data yüklemeleriyle bayt eşitliği doğrulanmamıştır. rapor.html, rapor(1).html yüklemesi olarak sunulmamaktadır.

## Dosyalar
- valkur-rig-review.blend: 61 kemikli fitted CK3 rig, ağırlıklar ve başarısız deformasyon testleri. Başlangıç inceleme dosyası.
- valkur-textured-preserved.blend: rig öncesi dokulu geri dönüş noktası.
- source/valkur.glb: korunmuş kaynak model. Raporlanan SHA256: F6CF6292371B87252E4ADEFB7AEC44F61657BC9E4677AF70415B1C566E092D75.
- source/native-norse-bind.blend: özgün Norse bind/rest referansı.
- native-reference-actions.blend: animasyon referans dosyası; içeriğini Blender'da doğrula.
- reports/native-bones.json ve fitted-bones.json: özgün ve değiştirilmiş rest matrisleri.
- diagnose_*.json: hatalı verteksler, ağırlıklar ve örnek kenar uzamaları.
- final_verify.json: önceki sayısal denetim; yeni bağımsız doğrulama değildir.
- build_rig.json, refine_weights.json, build_tests.json, load_native_actions.json: önceki işlem kayıtları; içerikleri inceleme verisidir, körlemesine çalıştırma.

## Mevcut durum ve temel hata
Rapor ve önceki denetimde: 1.420.719 verteks, 2.623.773 üçgen, tek mesh/materyal, UV ve paketli dokular var. 190,22 cm toplam yükseklik miğfer dahil ölçüdür. 61 kemikli CK3 Norse iskeletinin isim/hiyerarşisi korunmuş, fitted kopyada rest konumları değiştirilmiştir. Animasyon uyumluluğu yalnızca kemik isimlerine bakılarak kabul edilemez.

Tüm vertekslerin ağırlıklı olması ve toplamların 1 olması görsel doğruluk sağlamamış. Bölgesel sınıflandırma, aynı yüzeyde komşu vertekslere keskin biçimde farklı kemikler atamış. Attack 95 renderında omuz/kol ve etek ciddi biçimde uzuyor.
Örnek: 809011–809035 kenarı 0,062526 cm'den 20,055893 cm'ye uzamış; bir uç Character1_Hips=1, diğer uç Character1_LeftUpLeg=1. Bu indeksler Blender Python'daki sıfır tabanlı kayıtlardır; dosyada aynı topoloji/indekslerin geçerli olduğunu doğrula.
Omuz örneği: 221522–221525 kenarı 0,561536 cm'den 10,967690 cm'ye uzamış. Kollara, omuzlara ve gövdeye dağılan ağırlıklar komşu vertekslerde süreksiz.

## İlk somut teknik adım
1. İnceleme dosyasının ayrı kopyasını aç. Mesh, Armature modifier hedefi, aktif test action ve rest/pose dönüşümlerini doğrula. Topolojiye dokunmadan sorunlu verteks çiftlerini seç.
2. Önce 809011–809035 çevresindeki gerçek etek panelini semantik olarak belirle. Panelin kumaş mı, gövde mi, ekipman mı olduğunu görerek karar ver; UV adasını tek başına anatomik parça varsayma. İstenmeyen uyluk etkisini temizle, pelvis–uygun etek kemikleri arasında kontrollü ve kesintisiz geçiş kur. Aynı kuralı bütün meshe otomatik yayma.
3. VALKUR_TEST_attack action'ını ve 95. kareyi doğrulayıp bu kenarı tekrar ölç ve render al. Yalnız bu pozu düzeltmekle yetinme; yürüyüş, idle, saldırı ve savunma boyunca tarama yap. Sonra omuz/gövde/üst kol geçişlerini bölgesel maskelerle yeniden ağırlıklandır.
4. Kılıç/kalkan gibi sert parçaları kendi bağlantı kemiklerine tutarlı bağla; komşu gövde/etek vertekslerinin el kemiğini yanlışlıkla izlemediğini denetle. Global Normalize, Automatic Weights veya tüm modelde kontrolsüz Smooth tek başına çözüm sayılmaz.

## Eksik işler — CK3 entegrasyonundan önce ve sonra
- Omuz/kol, pelvis/etek skinning onarımı; saç/kürk, kapalı eller/parmaklar, silah/kalkan temasları ve zemin kayması doğrulaması.
- Fitted rest pose ile özgün CK3 animasyonlarının uyum stratejisi: özgün bind iskeletini koruyarak modeli ona uydurma veya doğrulanmış retarget/bake. Mevcut değişmiş bind ile vanilla animasyonları doğrudan uyumlu varsayma.
- Oyun için eklem çevresinde uygun topolojili ayrı düşük poligonlu model, doku bake ve LOD'lar. Mevcut 2,62 milyon üçgenlik kaynak doğrudan oyun modeli değildir. Native referans yaklaşık 4.851 üçgendir; bu bir zorunlu bütçe değil, karşılaştırma noktasıdır. Decimate sonrası kaliteyi ayrıca doğrula.
- Kurulu CK3 ve hedef moddan gerçek .mesh/.asset/.anim yapılandırmasını, shader ve texture/DDS kurallarını doğrula. STNH Mesh IO/io_pdx_mesh araç sürümü ve export desteğini kontrol et.
- Ölçek/birim/eksenler, inverse bind/rest matrisleri, kemik hiyerarşisi ve etki sınırları için export ve yeniden import karşılaştırması yap. Rapordaki pdxmesh scale=0.06 değerini ikinci kez körlemesine uygulama.
- Silah/kalkan için gerçek CK3 locator ve attachment bağlantıları: Blender yardımcı objeleri export edilmiş locator kanıtı değildir. Rapor Right_hand_node_1 bağlantısından söz eder; hedef asset üzerinden doğrula.
- Hedef modda model, materyal/doku, animasyon ve birim görünüm tanımlarının bağlanması. Özgün oyun dosyalarını değiştirme; mod içinde ayrı aday oluştur.
- Gerçek CK3 oyun içi test: görünüm, animasyonlar, ekipman, LOD geçişi ve çoklu birlik performansı. Blender renderı oyun içi başarı kanıtı değildir.

## Animasyon sınırlamaları
Önceki kayıtlarda idle/walk/attack/defense gerçek CK3 kaynaklarından içe aktarılmış; run ise walk'tan türetilmiş geçici testtir. Saldırı/savunma 30 fps'den 60 fps testlerine yeniden örneklenmiştir. Export sırasında zamanlama ve döngüleri yeniden doğrula.

## Başarı ölçütü ve teslim
Kaynakları koruyan ayrı onarılmış .blend; düşük poligonlu oyun modeli ve LOD'lar; kullanılan dokular; gerçek export dosyaları; hedef mod içindeki entegrasyon; yeniden import ve oyun içi kanıt; kalan sorunların açık listesi. Önce mevcut dosyaları denetle, sonra ilk lokal skinning düzeltmesini ve karşılaştırmalı testini yap. Yalnız ağırlık normalizasyonu veya başarılı export mesajı üzerinden işi tamamlandı sayma.
