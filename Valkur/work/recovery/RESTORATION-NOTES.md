# Valkür — geri yüklenen test sürümü

21 Ekim 2026. Durum: yan parçalar geri yüklendi ve mevcut **Valkur Units Test** moduna kuruldu. Bu sürüm tam oyun-hazır teslim değildir. Gerçek oyun içi test bu işlem sırasında yapılmadı.

## Adım adım yapılanlar

1. Devir raporu, kesme ve ağırlık düzeltme betikleri, işlem kayıtları ve mevcut dosyalar incelendi. Kayıt envanteri `records-index.json` içinde. Önceki başarılı-export mesajları görsel doğruluk kanıtı olarak kullanılmadı.
2. Değişiklik öncesi test modunun tamamı `mod-before-restoration/` altına kopyalandı. Mevcut mod meshinin hash'i, kurulum öncesinde bu yedekle tekrar karşılaştırıldı. Kaynak GLB ve önceki Blender dosyaları değiştirilmedi.
3. Kesilmemiş, dokuları ve mevcut yürüyüş düzenlemesini taşıyan `../valkur-walk-fix.blend` geri dönüş noktası seçildi. Kesilmiş sürümdeki 117.811 yüze karşı bu kopyada 124.741 yüz var. Yüz konumu karşılaştırmasıyla **6.930 silinmiş yüz** tespit edildi ve tamamı geri getirildi. Kanıt: `initial-audit.json`.
4. Kalkan, el ve etek arasındaki yanlış kemik etkileri ayrıldı. Kaynaşmış temas sınırlarında köşeler ayrılarak aynı yüzün bir ucunun eli, diğer ucunun kalçayı takip etmesi azaltıldı. Hiçbir yüz silinmedi; yüz köşelerinin dinlenme konumları ve UV değerleri kesilmemiş yedekle birebir aynı kaldı. Bu işlem topolojide sınır ayrımı içerir: 90.072 köşeden 91.927 köşeye çıkıldı. Yeni yüzey tasarlanmadı ve etek kısaltılmadı.
5. Sol kalça/etek ağırlıkları yalnız ilgili bölge içinde yumuşatıldı. Önkol–el geçişleri düzenlendi; önkoldaki kalça etkileri ve dirsekteki yanlış el etkileri temizlendi. Elin iç kenarı yakın plan dinlenme görüntüleri ve doku örnekleriyle incelendi. Etek kenarı ile parmaklar ayrı değerlendirilerek elin bir bölümünün kalça yanında kalması giderildi.
6. Dış omuz kürkündeki bazı yanlış baş/boyun etkileri azaltıldı. Bu düzeltme kürkün bütün savaş pozlarındaki sorunlarını çözmedi. Başka gövde denemesi son teslim dosyasına alınmadı.
7. Dört mevcut test action'ı boyunca toplam **878 kare** sayısal olarak tarandı: idle 179, walk 81, attack 309, defense 309. Seçili dinlenme, yürüme ve savaş kareleri render edilerek incelendi. Sayısal tarama her karenin görsel olarak onaylandığı anlamına gelmez.
8. Son aday `valkur-restored-final.blend` olarak kaydedildi ve `export/valkur.mesh` üretildi. Dosya boş bir Blender sahnesine yeniden içe alındı. Export girdisiyle konum, normal, tangent, UV, üçgen dizisi ve skin verileri eşleşti. Yeniden içe alınan kemik ağırlıklarında **0 uyuşmazlık**, sınır kutusunda **0 fark** bulundu. İskeletin export edilen rest verisi önceki oyun meshiyle aynı.
9. Kontrollerden geçen mesh mevcut moda kuruldu. Yalnız `gfx/models/units/infantry/valkur/valkur.mesh` değişti. Diğer **14 mod dosyası** hash karşılaştırmasıyla aynı: dokular, animasyonlar, asset ve entity bağlantıları korunuyor. Kurulum kaydı: `deployment.json`.

## Dosyalar ve kanıtlar

- Düzenlenebilir teslim: `valkur-restored-final.blend`. Dokular paketli; rig ve mevcut test action'ları içeride. Armature başlangıçta REST modunda; animasyon izlerken POSE seçilmelidir.
- Son çalışma adayı: `valkur-restored-collar.blend`.
- Oyun çıktısı ve mevcut DDS kopyaları: `export/`.
- Son animasyon/koruma denetimi: `validation-collar.json`.
- Export ve bağımsız yeniden içe alma denetimi: `roundtrip.json`.
- Yürüyüş önizlemesi: `collar-walk-20.png`.
- Saldırı 95 önizlemesi: `collar-attack-95.png`.
- Kalan zor poz örneği: `collar-attack-218.png`.
- Ön/arka dinlenme şekli: `review-front.png`, `review-back.png`. Bu görüntüler aynı dinlenme geometrisine sahip daha erken adaydan; son ağırlık düzeltmeleri dinlenme şeklini değiştirmedi.
- Eski kurulu modun tam kopyası: `mod-before-restoration/`.

Kaynak GLB SHA256 tekrar doğrulandı: `F6CF6292371B87252E4ADEFB7AEC44F61657BC9E4677AF70415B1C566E092D75`.

Kurulan mesh SHA256: `DE4B555D18116BCF12379B886F7AD085DEDC1C54033E511A9A0DCD337D21C5D7`.

## Denetimin kapsamı ve kalan sorunlar

Sol etek için tanımlı kontrol bölgesindeki en büyük ek kenar uzunluğu, kesilmemiş yedekten son adaya: yürüyüşte yaklaşık 39,20 → 3,06 cm; saldırıda 106,31 → 5,70 cm; savunmada 82,20 → 5,12 cm. Bu değerler tüm karakter için kalite puanı değildir. Temas sınırlarının ayrılması bağlantı yapısını değiştirdiği için ölçümler render incelemesiyle birlikte değerlendirilmelidir.

Son adayda 61 kemik, en fazla dört etki/köşe ve sıfır ağırlıksız köşe doğrulandı. Önceki fitted rest matrisleri korundu. Bu, vanilla animasyonların değiştirilmiş bind ile genel uyumluluğunun yeniden kanıtlandığı anlamına gelmez; yalnız mevcut test modunun iskeletini korur.

**Hâlâ çözülmesi gerekenler:**

- Bazı uç saldırı/savunma pozlarında gövde–koltuk altı, sırt/saç ve kürk geçişlerinde belirgin gerilme var. Örneğin geniş gövde kontrol bölgesinin en büyük ek kenar uzunluğu saldırıda yaklaşık 23,62 cm, savunmada 25,58 cm. Omuz kürkü bölgesinde de yaklaşık 20–22 cm'ye çıkan örnekler var. Model bu yüzden tamamen düzelmiş sayılmadı.
- Kalkan tutuşu ve elin hareketi iyileşti; bütün animasyonlarda temas, penetrasyon ve parmak kalitesi onaylanmış değil. Kaynak modelin kaynaşmış el/ekipman/giysi temasları daha düzenli topoloji gerektirebilir. Bu kusurları gizlemek için yeni yüz silme yapılmamalı.
- Export **179.982 üçgen** ve UV/normal sınırları nedeniyle **134.679 export köşesi** içeriyor. Bu bir test modelidir. Üretim için düşük poligonlu retopoloji, LOD ve çoklu birlik performans testi eksik.
- Animasyon zamanlaması, zemin kayması ve oyun durum geçişleri bu düzeltmede yeniden tasarlanmadı. Mevcut `.asset` içindeki `besiege` durumu idle animasyonunu kullanıyor; özel kuşatma/yağmalama animasyonu eklendiği iddia edilmiyor.
- Gerçek export locator/attachment çalışması bu adımın parçası değil. Mevcut kılıç/kalkan model parçaları korunuyor.
- Blender görüntüsü, CK3 oyun içi doğrulaması değildir. Son kurulumun oyunda yeniden yüklenip denenmesi gerekiyor.

## Ortam ve test

Blender: yerel 5.2.2. Export: mevcut STNH/io_pdx_mesh eklentisinin çalışma alanındaki kopyası. Export sırasını koruyan sözlük/set aramalarıyla yavaş köşe aramaları hızlandırıldı; küçük UV küpünde özgün fonksiyonla çıktı eşitliği ve gerçek modelde export/yeniden import eşitliği kontrol edildi. Kurulu Blender eklentisi değiştirilmedi.

Yerel CK3 launcher metadata'sı `C:\Game\Crusader Kings 3\launcher\launcher-settings.json` içinde `rawVersion=1.20.0.2`; test modunun destek bildirimi `1.20.*`. Çalışan oyun menüsünden sürüm doğrulaması yapılmadı. `pdxmesh scale=0.06` mevcut asset içinde aynen korundu, ikinci bir ölçek uygulanmadı.

Oyunu tamamen kapatıp **Valkur Units Test** etkin halde yeniden açın. Var olan test birliğinde önce idle ve yürüyüş sırasında iki yan eteği, sonra kalkanlı kolu farklı açılardan kontrol edin. Ardından savaş sırasında saldırı ve savunmayı inceleyin. Bu modun mevcut entity bağlantısı Northern Lords `fp1_army_01` Norse levy görünümünü değiştirir; bütün kültür/birim varyantlarına uygulanmaz.

Yeni karakter eklerken `gfx/models/units/infantry/<benzersiz_ad>/` altında ayrı mesh/texture/anim/asset dizini ve benzersiz entity/pdxmesh adları kullanılmalıdır. Valkür dosyalarının üstüne başka model yazılmamalıdır. Mevcut `entity_links/valkur_units_test.txt` bu ayrımı destekleyen başlangıç yapısını içerir.

## Yeniden üretim ve devam noktası

Başarılı zincir: kesilmemiş `valkur-walk-fix.blend` → `restore_split3.py` → `smooth_side.py` → son `separate_limb_contacts.py` → `repair_collar.py` → `export_restored.py` → `roundtrip.py`. Betikler geçmiş deneme çıktıları da üretir; herhangi bir betiği yanlış başlangıç dosyasında körlemesine çalıştırmayın.

`valkur-restored-limbs.blend`, contacts1/2 ve `valkur-restored-torso.blend` gibi ara denemeler teslim değildir. Kurulu mesh, `valkur-restored-collar.blend` üzerinden üretilen `valkur-restored-final.blend` ile eşleşir. Devam ederken yeni bir çalışma kopyası oluşturun; kaynakları ve bu doğrulanmış test sürümünü koruyun.
