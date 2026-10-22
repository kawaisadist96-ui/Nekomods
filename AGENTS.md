# Nekomods — Agent çalışma kuralları

## Amaç
Bu depo, CK3 modları ve Blender tabanlı karakter/animasyon geliştirmeleri için ortak çalışma alanıdır. Öncelik: bir ajanın kullanım kotası dolduğunda başka ajanın **kesintisiz devam edebilmesi**.

## Her görevin başında
1. README.md, PROJECT_STATUS.md, HANDOVER.md ve KNOWN_ISSUES.md dosyalarını oku.
2. İlgili mod klasörünü ve son commitleri incele.
3. GitHub'daki kayıtlarla gerçek dosyaların durumunu karşılaştır; bulunmayan dosyaları var sayma.
4. Tek bir somut görev belirle ve mümkünse onu tamamla.

## Çalışma kuralları
- Önce mevcut çalışır durumu koru; gereksiz yeniden yazma yapma.
- Blender rig/animasyon ve CK3 entegrasyonu hakkında test edilmemiş sonuçları 'tamamlandı' diye kaydetme.
- Aynı dosyada eşzamanlı çalışan ajanlar birbirinin değişikliklerini ezmemeli. Paralel işlerde ayrı branch ve PR kullan.
- Kullanıcı istemedikçe lisans, repo görünürlüğü veya proje kapsamını değiştirme.
- CK3'e ait üçüncü taraf oyun varlıklarını yüklemeden önce dağıtım hakkını kontrol et.
- Büyük ikili dosyalar için Git LFS ihtiyacını değerlendir.
- Her anlamlı değişiklikten sonra commit/push yap; yerelde kalan çalışma diğer ajanlara görünmez.
- Gizli anahtarları, erişim tokenlarını ve kişisel bilgileri depoya koyma.

## Görev devri zorunluluğu
Bir oturumun sonunda, özellikle kota bitmeden önce:
1. Kod ve diğer dosyaları commit/push yap (mümkünse).
2. PROJECT_STATUS.md içindeki doğrulanmış durumu güncelle.
3. HANDOVER.md dosyasına son görev, değişen dosyalar, test sonuçları, kalan adımlar ve bilinen engelleri yaz.
4. Yeni hata varsa KNOWN_ISSUES.md'ye ekle.
5. Sonraki ajana kısa ve uygulanabilir bir 'ilk adım' bırak.

## Doğrulama
İşin tamamlandığı iddiası için test yöntemi ve sonucu yazılmalı. Test mümkün değilse 'test edilmedi' denmeli.
