# Devam noktası — 22 Ekim 2026

GÜNCEL: Vanilla Norse askerin 26 klibi ve 27 state bloğu Valkür'e uyarlandı; mevcut Valkur Units Test moduna kuruldu. Oyun içi test henüz yapılmadı.

Güncel düzenlenebilir dosya: `work/vanilla-integration/valkur-vanilla-equipment.blend`. Borulu önizleme: `work/vanilla-integration/valkur-vanilla-preview.blend`.

Adımlar, kanıtlar ve kalan sorunlar: [INTEGRATION-NOTES.md](work/vanilla-integration/INTEGRATION-NOTES.md). Kurulum: `work/vanilla-integration/deployment.json`; önceki mod yedeği: `work/vanilla-integration/mod-before/`. Geri getirilen yüzler ve DDS dokular korundu. Aşağıdaki kayıt önceki onarım sürümüne aittir; güncel kurulumun dosyalarını tanımlamaz.

## Önceki onarım kaydı

Yanlardan fazla kesilen 6.930 yüz geri yüklendi. Düzenlenebilir son test dosyası `work/recovery/valkur-restored-final.blend`; mevcut Valkur Units Test moduna kurulan mesh `work/recovery/export/valkur.mesh` ile aynı.

Adım adım değişiklikler, doğrulamalar, kurulum ve kalan sorunlar: [RESTORATION-NOTES.md](work/recovery/RESTORATION-NOTES.md).

Bu sürüm tam oyun-hazır değildir. Uç saldırı/savunma pozlarında gövde, koltuk altı, sırt/saç ve kürk sorunları sürüyor. LOD ve oyun içi test henüz yapılmadı. Modeli tekrar keserek bu sorunları gizlemeyin. Yüz konumları/UV koruması ve kurulu mod yedeği mevcut.

Son başarılı kaynak `work/recovery/valkur-restored-collar.blend`. `valkur-restored-torso.blend` ve önceki denemeler kurulu sürüm değildir. Kurulum kanıtı `work/recovery/deployment.json`; son tam animasyon taraması `work/recovery/validation-collar.json`; yeniden import kanıtı `work/recovery/roundtrip.json`.
