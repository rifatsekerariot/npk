# NPK Sensor Monitor

IoT sistemi ile Raspberry Pi Zero 2W üzerinde RS485 protokolü ile NPK (Azot-Fosfor-Potasyum) toprak sensöründen veri okuyarak ThingsBoard platformuna MQTT ile gönderen uygulama.

![System Architecture](https://img.shields.io/badge/Platform-Raspberry%20Pi-C51A4A?logo=raspberry-pi)
![Python](https://img.shields.io/badge/Python-3.7+-3776AB?logo=python&logoColor=white)
![MQTT](https://img.shields.io/badge/Protocol-MQTT-660066)
![ThingsBoard](https://img.shields.io/badge/IoT-ThingsBoard-orange)

## 📋 İçindekiler

- [Özellikler](#özellikler)
- [Donanım Gereksinimleri](#donanım-gereksinimleri)
- [Kurulum](#kurulum)
- [Konfigürasyon](#konfigürasyon)
- [Kullanım](#kullanım)
- [ThingsBoard Kurulumu](#thingsboard-kurulumu)
- [Sorun Giderme](#sorun-giderme)

## ✨ Özellikler

- 🌱 **NPK Sensör Okuma**: RS485/Modbus RTU protokolü ile Azot, Fosfor, Potasyum değerlerini okuma
- ☁️ **ThingsBoard Entegrasyonu**: MQTT protokolü ile gerçek zamanlı veri iletimi
- 📱 **Mobil Erişim**: ThingsBoard mobil app ile her yerden izleme
- 🔄 **Otomatik Yeniden Bağlanma**: Bağlantı kopması durumunda otomatik recovery
- 📊 **Opsiyonel Dashboard**: Streamlit ile lokal monitoring arayüzü
- 🚀 **Zero-Touch Kurulum**: Tek script ile tam otomatik kurulum
- 🔧 **Systemd Servisi**: Otomatik başlatma ve crash recovery

## 🛠️ Donanım Gereksinimleri

### Gerekli Donanımlar

1. **Raspberry Pi Zero 2W**
   - RAM: 512 MB
   - WiFi: 2.4 GHz 802.11 b/g/n
   - Bluetooth: 4.2, BLE

2. **Waveshare RS485 CAN HAT**
   - RS485 transceiver
   - UART arayüzü (GPIO 14/15)

3. **NPK Sensör**
   - RS485 Modbus RTU protokolü
   - Güç: 12-24V DC
   - Ölçüm aralığı: Yaprak modeline göre

4. **Güç Kaynağı**
   - Raspberry Pi için: 5V 2.5A USB
   - Sensör için: 12V veya 24V DC adaptör

### Donanım Bağlantı Şeması

```
NPK Sensor (RS485)          Waveshare RS485 HAT      Raspberry Pi Zero 2W
┌──────────────┐            ┌─────────────────┐      ┌──────────────┐
│              │            │                 │      │              │
│ VCC (12-24V) ├────────────┤ External PSU    │      │              │
│ GND          ├────────────┤ GND             ├──────┤ GND (Pin 6)  │
│ A+           ├────────────┤ A               │      │              │
│ B-           ├────────────┤ B               │      │              │
│              │            │ TXD             ├──────┤ GPIO14 (P8)  │
│              │            │ RXD             ├──────┤ GPIO15 (P10) │
│              │            │ VCC             ├──────┤ 5V (Pin 2)   │
└──────────────┘            └─────────────────┘      └──────────────┘
```

## 📦 Kurulum

### Zero-Touch Kurulum (Önerilen)

1. **Projeyi Raspberry Pi'ye aktarın:**

   ```bash
   # USB veya SCP ile dosyaları kopyalayın
   cd ~
   git clone https://github.com/rifatsekerariot/npk.git
   cd npk
   ```

2. **Kurulum scriptini çalıştırın:**

   ```bash
   sudo chmod +x install.sh
   sudo ./install.sh
   ```

3. **İşlem adımları:**
   - Sistem güncellemesi
   - Python bağımlılıklarının kurulumu
   - RS485 UART konfigürasyonu
   - Uygulama dosyalarının kopyalanması
   - Systemd service kurulumu
   - Konfigürasyon düzenleme

4. **Sistemi yeniden başlatın:**

   ```bash
   sudo reboot
   ```

### Manuel Kurulum

Detaylı manuel kurulum adımları için [MANUAL_INSTALL.md](docs/MANUAL_INSTALL.md) dosyasına bakın.

## ⚙️ Konfigürasyon

Konfigürasyon dosyası: `/etc/npk-monitor/config.yaml`

### Temel Ayarlar

```yaml
# NPK Sensör Ayarları
sensor:
  port: '/dev/ttyS0'          # RS485 HAT'in kullandığı port
  slave_id: 1                 # Modbus slave ID
  baudrate: 4800              # Baud rate (genelde 4800 veya 9600)
  
  # Modbus register adresleri (sensör modeline göre)
  registers:
    nitrogen: 0x001E
    phosphorus: 0x001F
    potassium: 0x0020

# ThingsBoard Ayarları
thingsboard:
  host: 'demo.thingsboard.io' # ThingsBoard server
  access_token: 'YOUR_TOKEN'  # Device access token

# Uygulama Ayarları
application:
  reading_interval: 60        # Okuma aralığı (saniye)
```

### ThingsBoard Token Alma

1. ThingsBoard'a giriş yapın
2. Devices > Add Device (+)
3. Device adı girin ve kaydedin
4. Device'a tıklayın > Copy Access Token
5. Token'ı `config.yaml` dosyasına yapıştırın

Detaylı ThingsBoard kurulumu için: [THINGSBOARD_SETUP.md](docs/THINGSBOARD_SETUP.md)

## 🚀 Kullanım

### Servis Yönetimi

```bash
# Servisi başlat
sudo systemctl start npk-monitor

# Servisi durdur
sudo systemctl stop npk-monitor

# Servis durumunu kontrol et
sudo systemctl status npk-monitor

# Servisi yeniden başlat
sudo systemctl restart npk-monitor

# Boot'ta otomatik başlatmayı etkinleştir/devre dışı bırak
sudo systemctl enable npk-monitor
sudo systemctl disable npk-monitor
```

### Log İzleme

```bash
# Canlı log takibi
tail -f /var/log/npk-monitor/npk-monitor.log

# Hata logları
tail -f /var/log/npk-monitor/npk-monitor.error.log

# Systemd journal
sudo journalctl -u npk-monitor -f

# Son 100 satır
sudo journalctl -u npk-monitor -n 100
```

### Manuel Test

```bash
# Sensör bağlantı testi
cd /opt/npk-monitor
python3 src/npk_reader.py --test

# Tek seferlik okuma
python3 src/npk_reader.py

# Sürekli okuma (5 saniye aralıkla)
python3 src/npk_reader.py --continuous --interval 5

# MQTT bağlantı testi
python3 src/mqtt_publisher.py --host demo.thingsboard.io --token YOUR_TOKEN --test
```

### Streamlit Dashboard (Opsiyonel)

Lokal monitoring için:

```bash
cd /opt/npk-monitor
streamlit run dashboard/dashboard.py
```

Tarayıcıda açılacak URL'yi kullanarak dashboard'a erişin (genelde `http://localhost:8501`).

## 📱 ThingsBoard Kurulumu

### 1. Device Oluşturma

1. ThingsBoard'a giriş yapın
2. **Devices** > **Add Device (+)**
3. Device bilgilerini girin:
   - Name: `NPK Sensor 01`
   - Device Profile: Default
4. **Add** butonuna tıklayın
5. **Copy Access Token** butonuna tıklayıp token'ı kaydedin

### 2. Dashboard Oluşturma

1. **Dashboards** > **Add Dashboard (+)**
2. Dashboard adı: `NPK Monitoring`
3. **Add Widget** butonuna tıklayın
4. Widget türünü seçin (örn: **Cards** > **Latest values**)
5. Data source olarak device'ı seçin
6. Telemetri anahtarlarını seçin: `nitrogen`, `phosphorus`, `potassium`

### 3. Mobil Erişim

1. **ThingsBoard Mobile App** indirin (iOS/Android)
2. Server URL girin (örn: `https://demo.thingsboard.io`)
3. Kullanıcı adı ve şifre ile giriş yapın
4. Dashboard'ları görüntüleyin

Detaylı kurulum: [THINGSBOARD_SETUP.md](docs/THINGSBOARD_SETUP.md)

## 🔧 Sorun Giderme

### Sensör Bağlantı Hataları

**Problem:** `Error reading register` hatası

**Çözüm:**

- RS485 kablolarını kontrol edin (A+ ve B- doğru bağlı mı?)
- Baud rate ayarını kontrol edin (4800 veya 9600)
- Slave ID'nin doğru olduğunu doğrulayın
- External power supply'ın çalıştığını kontrol edin

### UART Çalışmıyor

**Problem:** `/dev/ttyS0` bulunamıyor

**Çözüm:**

```bash
# UART'ın etkin olduğunu kontrol edin
ls -l /dev/ttyS0

# config.txt'yi kontrol edin
sudo nano /boot/config.txt
# enable_uart=1 satırının varlığını kontrol edin

# Serial console'un devre dışı olduğunu kontrol edin
sudo systemctl status serial-getty@ttyS0.service
# (disabled olmalı)

# Sistemi yeniden başlatın
sudo reboot
```

### MQTT Bağlantı Hataları

**Problem:** `Connection refused` veya `Authentication failed`

**Çözüm:**

- ThingsBoard host adresini kontrol edin
- Access token'ın doğru olduğunu doğrulayın
- İnternet bağlantısını kontrol edin
- Firewall ayarlarını kontrol edin

### Servis Başlamıyor

**Problem:** Service failed to start

**Çözüm:**

```bash
# Detaylı hata mesajını görüntüleyin
sudo journalctl -u npk-monitor -n 50

# Manuel olarak çalıştırıp hataları görün
cd /opt/npk-monitor
python3 src/main.py --config /etc/npk-monitor/config.yaml

# İzinleri kontrol edin
ls -l /opt/npk-monitor/src/
chmod +x /opt/npk-monitor/src/*.py
```

Daha fazla sorun giderme: [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📂 Dosya Yapısı

```
npk-monitor/
├── src/
│   ├── main.py              # Ana uygulama
│   ├── npk_reader.py        # Sensör okuma modülü
│   └── mqtt_publisher.py    # MQTT client modülü
├── config/
│   └── config.yaml          # Konfigürasyon
├── dashboard/
│   └── dashboard.py         # Streamlit dashboard
├── systemd/
│   └── npk-monitor.service  # Systemd service
├── docs/
│   ├── THINGSBOARD_SETUP.md
│   └── TROUBLESHOOTING.md
├── install.sh               # Kurulum scripti
├── requirements.txt         # Python bağımlılıkları
└── README.md               # Bu dosya
```

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için önce bir issue açarak değişikliği tartışın.

## 📄 Lisans

[MIT](LICENSE)

## 👤 İletişim

Sorularınız için issue açabilirsiniz.

---

**Not:** Bu proje Raspberry Pi Zero 2W ve Waveshare RS485 HAT için optimize edilmiştir. Diğer Raspberry Pi modelleri ve RS485 HAT'ler için konfigürasyon ayarları gerekebilir.
