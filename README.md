# Göz Takip ve Fare Kontrol Sistemi

Bu proje, göz hareketlerinizi kullanarak bilgisayar faresini kontrol etmenizi sağlar.

## Kurulum ve Çalıştırma Sırası

Projeyi başka bir bilgisayarda çalıştırmak için aşağıdaki adımları **sırasıyla** takip edin:

### 1. Kalibrasyon Verisi Toplama
Öncelikle sistemin gözlerinizi tanıması ve ekran koordinatlarıyla eşleştirmesi gerekir.
*   **Çalıştırılacak Dosya:** `calibration_capture.py`
*   **Ne Yapılacak:** Ekranınızda beliren kırmızı noktalara (9 adet) sırayla bakın. Her nokta için sistem kısa bir süre veri toplayacaktır.
*   **Sonuç:** `../data/raw/calibration.csv` dosyası oluşturulur.

### 2. Modeli Eğitme
Toplanan verileri kullanarak yapay zeka modelini eğitmeniz gerekir.
*   **Çalıştırılacak Dosya:** `train_calibration.py`
*   **Ne Yapılacak:** Sadece dosyayı çalıştırın.
*   **Sonuç:** `../data/models/calibration_model.pkl` dosyası oluşturulur.

> **Not:** 1. ve 2. adımları sadece ilk kurulumda veya kalibrasyonun bozulduğunu hissettiğinizde yapmanız yeterlidir.

### 3. Uygulamayı Başlatma
Artık ana uygulamayı kullanabilirsiniz.
*   **Çalıştırılacak Dosya:** `gui_app.py`
*   **Ne Yapılacak:**
    1.  Açılan pencerede **"Başlat"** butonuna basın.
    2.  **Ayarlar** sekmesinden hassasiyeti (Smoothing) ve tıklama ayarlarını kişiselleştirebilirsiniz.
    3.  **Kullanım:**
        *   **İmleç Hareketi:** Gözlerinizle ekrana bakın.
        *   **Sol Tık:** Sol gözünüzü hızlıca iki kere kırpın.
        *   **Sağ Tık:** Sağ gözünüzü hızlıca iki kere kırpın (Ayarlardan açılabilir).

## Gereksinimler
Projenin çalışması için aşağıdaki Python kütüphanelerinin yüklü olması gerekir:
```bash
pip install opencv-python mediapipe numpy pynput pyautogui joblib pyqt5 pandas sklearn
```
