# Nekomods — Bilinen sorunlar

## Açık
### ISSUE-001 — İlk kaynak aktarımı
- Durum: Valkür kaynakları ve geçmiş çalışmalar Valkur/ altında aktarıma hazırlandı; Git LFS indirmesi gerekir. Higanbana kaynakları henüz aktarılmadı.
- Sonraki adım: Başka makinede klonlama ve Git LFS indirmesini doğrula.

### ISSUE-002 — Valkür animasyon sorunları (kullanıcı bildirimi)
- Belirtiler: Yürüyüşte doğal olmayan diz hareketleri; kalkan kavrama ve kılıç konumlandırma.
- Kanıt: Önceki kullanıcı geri bildirimi; bu depoda yeniden test edilmedi.
- Sonraki adım: Model, rig, animasyon dosyaları ve oyun içi çıktılarla sorunu yeniden üret.

### ISSUE-003 — Vanilla entegrasyonu sonrası ekipman hizası
- Durum: Açık; kullanıcının son oyun görüntüsünde doğrulandı.
- Belirti: Kalkanın el/ön kol açısı doğal değil. Beldeki kılıç yanlış yerde ve açıyla bacak bölgesine taşıyor.
- İlgili dosyalar: Valkur/work/vanilla-integration/equipment.py, valkur-vanilla-equipment.blend; valkur_shield.mesh ve valkur_sword_stowed.mesh.
- Sonraki adım: Ekipman yerel dönüşümlerini düzelt; idle, yürüyüş, toplama, terhis ve saldırıda karşılaştır. Çalışan 26 klibi yeniden tasarlama.

### ISSUE-004 — Model kalitesi ve taşınabilirlik
- Uç pozlarda koltuk altı, kürk/saç ve ekipman teması sorunları kalabilir. LOD ve çoklu birlik performansı tamamlanmadı.
- Scriptlerde Blender/oyun/mod için yerel mutlak yollar bulunur. Temiz makinede otomatik build doğrulanmadı.

## Kayıt şablonu
### ISSUE-XXX — Kısa başlık
- Durum:
- Belirti:
- Tekrarlama adımları:
- İlgili dosyalar:
- Denenen çözümler:
- Sonraki adım:
