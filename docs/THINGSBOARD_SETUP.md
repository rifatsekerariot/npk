# ThingsBoard Kurulum Rehberi

Bu dokümantasyon, NPK sensör verilerinizi ThingsBoard platformunda görüntülemek için gerekli adımları içerir.

## İçindekiler

- [ThingsBoard Seçenekleri](#thingsboard-seçenekleri)
- [Device Oluşturma](#device-oluşturma)
- [Dashboard Oluşturma](#dashboard-oluşturma)
- [Widget Konfigürasyonu](#widget-konfigürasyonu)
- [Mobil Erişim](#mobil-erişim)
- [Alarm Kuralları](#alarm-kuralları)

## ThingsBoard Seçenekleri

### 1. ThingsBoard Cloud (Önerilen - Başlangıç için)

**Demo Server:**

- URL: `https://demo.thingsboard.io`
- Ücretsiz hesap oluşturabilirsiniz
- Test ve geliştirme için idealdir
- UYARI: Demo sunucudaki veriler düzenli olarak silinir

**ThingsBoard Cloud:**

- URL: `https://thingsboard.cloud`
- Profesyonel kullanım için
- Ücretli planlar mevcut
- Garantili uptime ve support

### 2. Self-Hosted ThingsBoard

Kendi sunucunuzda çalıştırmak için:

```bash
# Docker ile kurulum
docker run -it -p 9090:9090 -p 1883:1883 -p 5683:5683/udp \
  -v ~/.mytb-data:/data -v ~/.mytb-logs:/var/log/thingsboard \
  --name mytb --restart always thingsboard/tb-postgres
```

Detaylı kurulum: <https://thingsboard.io/docs/user-guide/install/docker/>

## Device Oluşturma

### Adım 1: ThingsBoard'a Giriş

1. Tarayıcınızda ThingsBoard'a gidin (örn: `https://demo.thingsboard.io`)
2. Kullanıcı adı ve şifre ile giriş yapın
3. Ana sayfaya yönlendirileceksiniz

### Adım 2: Yeni Device Ekle

1. Sol menüden **Devices** sekmesine tıklayın
2. Sağ üstteki **+** (Add Device) butonuna tıklayın
3. Device bilgilerini doldurun:
   - **Name**: `NPK Sensor 01` (veya istediğiniz isim)
   - **Label**: `Field A - NPK` (opsiyonel)
   - **Device Profile**: `default` seçin
4. **Add** butonuna tıklayın

### Adım 3: Access Token Alma

1. Oluşturduğunuz device'a tıklayın
2. **Copy Access Token** butonuna tıklayın veya
3. **DETAILS** sekmesinden manuel olarak kopyalayın

```bash
# Örnek access token
A1B2C3D4E5F6G7H8I9J0
```

1. Bu token'ı `config.yaml` dosyasına yapıştırın:

```yaml
thingsboard:
  host: 'demo.thingsboard.io'
  access_token: 'A1B2C3D4E5F6G7H8I9J0'  # Buraya yapıştırın
```

## Dashboard Oluşturma

### Adım 1: Yeni Dashboard

1. Sol menüden **Dashboards** sekmesine tıklayın
2. **+** (Add Dashboard) butonuna tıklayın
3. Dashboard adı: `NPK Soil Monitoring`
4. **Add** butonuna tıklayın

### Adım 2: Dashboard'u Açın

1. Oluşturduğunuz dashboard'a tıklayın
2. Sağ altta **Edit mode** (kalem ikonu) butonuna tıklayın

## Widget Konfigürasyonu

### Widget 1: Latest Values - NPK Değerleri

1. **Add new widget** butonuna tıklayın
2. **Cards** kategorisinden **Latest values** seçin
3. **Add datasource** tıklayın:
   - Type: `Device`
   - Device: `NPK Sensor 01` seçin
4. **Add** tıklayın ve telemetry keys seçin:
   - ✓ `nitrogen`
   - ✓ `phosphorus`
   - ✓ `potassium`
5. **Advanced** sekmesinden:
   - Units: `mg/kg`
   - Decimals: `0`
6. **Add** butonuna tıklayın

### Widget 2: Time Series Chart - NPK Grafikleri

1. **Add new widget** butonuna tıklayın
2. **Charts** kategorisinden **Time series - Line chart** seçin
3. Data source olarak device'ı seçin
4. Telemetry keys:
   - `nitrogen` (Renk: Mavi)
   - `phosphorus` (Renk: Turuncu)
   - `potassium` (Renk: Yeşil)
5. **Settings** sekmesinden:
   - Time window: `Last 24 hours`
   - Aggregation: `Average`
   - Interval: `1 hour`
6. **Add** butonuna tıklayın

### Widget 3: Gauge - Nitrogen Göstergesi

1. **Add new widget** butonuna tıklayın
2. **Analogue gauges** kategorisinden **Radial gauge** seçin
3. Data source: Device > `NPK Sensor 01`
4. Key: `nitrogen`
5. **Settings**:
   - Min value: `0`
   - Max value: `200`
   - Units: `mg/kg`
   - Segments:
     - 0-60: Düşük (Kırmızı)
     - 60-120: Orta (Sarı)
     - 120-200: Yüksek (Yeşil)
6. **Add** butonuna tıklayın

Aynı şekilde Phosphorus ve Potassium için de gauge widget'ları oluşturun.

### Widget 4: Entities Table - Tüm Değerler

1. **Add new widget** butonuna tıklayın
2. **Entity widgets** > **Entities table** seçin
3. Device'ı seçin
4. Columns ekleyin:
   - `nitrogen`
   - `phosphorus`
   - `potassium`
   - `temperature` (varsa)
   - `moisture` (varsa)
   - `ph` (varsa)

### Dashboard Layout Örneği

```
┌─────────────────────────────────────────────────────────┐
│  NPK Soil Monitoring Dashboard                          │
├──────────────┬──────────────┬─────────────┬─────────────┤
│  Nitrogen    │  Phosphorus  │  Potassium  │  Status     │
│  [Gauge]     │  [Gauge]     │  [Gauge]    │  [Cards]    │
├──────────────┴──────────────┴─────────────┴─────────────┤
│  NPK Values Over Time                                    │
│  [Time Series Chart - 24H]                               │
├──────────────────────────────────────────────────────────┤
│  All Sensor Readings                                     │
│  [Entities Table]                                        │
└──────────────────────────────────────────────────────────┘
```

## Mobil Erişim

### iOS

1. App Store'dan **ThingsBoard** uygulamasını indirin
2. Uygulamayı açın
3. Server URL girin:
   - Demo: `https://demo.thingsboard.io`
   - Cloud: `https://thingsboard.cloud`
   - Self-hosted: `http://your-server-ip:9090`
4. Kullanıcı adı ve şifre ile giriş yapın
5. **Dashboards** sekmesine gidin
6. Dashboard'unuzu görüntüleyin

### Android

1. Google Play'den **ThingsBoard** uygulamasını indirin
2. iOS ile aynı adımları takip edin

### QR Code ile Hızlı Erişim

Dashboard'u mobil cihazdan hızlıca açmak için:

1. ThingsBoard web arayüzünde dashboard'u açın
2. Share butonuna tıklayın
3. QR Code oluşturun
4. Mobil cihazdan QR kodu tarayın

## Alarm Kuralları

NPK değerleri kritik seviyelere ulaştığında alarm almak için:

### Nitrogen Low Alarm

1. **Rule chains** > **Root Rule Chain** açın
2. Yeni rule node ekleyin: **Filter Script**
3. Script:

```javascript
return msg.nitrogen < 60;
```

1. Alarm node ekleyin: **Create Alarm**
   - Alarm type: `Nitrogen Low`
   - Severity: `WARNING`
   - Message: `Nitrogen level is critically low: ${nitrogen} mg/kg`

2. Email notification için **Send Email** node ekleyin

### Phosphorus High Alarm

```javascript
return msg.phosphorus > 150;
```

Alarm type: `Phosphorus High`, Severity: `CRITICAL`

## Test Etme

### 1. Manuel Veri Gönderme (Test)

```bash
# Sensör olmadan test için
mosquitto_pub -h demo.thingsboard.io -p 1883 \
  -u 'YOUR_ACCESS_TOKEN' -t v1/devices/me/telemetry \
  -m '{"nitrogen":95,"phosphorus":65,"potassium":82}'
```

### 2. Dashboard'u Kontrol Edin

1. Dashboard'u açın
2. Verilerin geldiğini doğrulayın
3. Grafiklerin güncellendiğini kontrol edin

### 3. Gerçek Zamanlı İzleme

1. NPK monitor servisini başlatın:

```bash
sudo systemctl start npk-monitor
```

1. Dashboard'da canlı veri akışını izleyin
2. Logları kontrol edin:

```bash
tail -f /var/log/npk-monitor/npk-monitor.log
```

## İleri Seviye Özellikler

### 1. Data Aggregation

Veri saklama maliyetini düşürmek için:

1. **Device profile** oluşturun
2. **Data aggregation** ayarlarını yapılandırın
3. Örnek: Saatlik ortalama değerleri sakla

### 2. Remote Commands

ThingsBoard'dan Raspberry Pi'ye komut göndermek için:

```python
# mqtt_publisher.py içine ekleyin
def on_rpc_request(client, userdata, message):
    data = json.loads(message.payload)
    method = data['method']
    params = data['params']
    
    if method == 'read_sensor':
        # Sensörü oku
        result = {"success": True}
        client.publish('v1/devices/me/rpc/response/' + data['requestId'], 
                      json.dumps(result))
```

### 3. Dashboard Paylaşımı

Public dashboard oluşturmak için:

1. Dashboard settings > **Make public**
2. Public link'i kopyalayın
3. Link'i paylaşın (giriş gerektirmeden erişim)

## Sorun Giderme

### Veri Gelmiyor

```bash
# MQTT bağlantısını test edin
python3 src/mqtt_publisher.py --host demo.thingsboard.io \
  --token YOUR_TOKEN --test
```

### Widget Boş

- Time window'u kontrol edin (Last 24H > Last 1H)
- Telemetry keys'lerin doğru olduğunu kontrol edin
- Device'ın aktif olduğunu doğrulayın

### Mobil App Bağlanamıyor

- Server URL'nin doğru olduğunu kontrol edin
- HTTPS kullanmayı deneyin
- Firewall ayarlarını kontrol edin

## Faydalı Linkler

- [ThingsBoard Docs](https://thingsboard.io/docs/)
- [MQTT API Reference](https://thingsboard.io/docs/reference/mqtt-api/)
- [Widget Development](https://thingsboard.io/docs/user-guide/contribution/widgets-development/)
- [Rule Engine](https://thingsboard.io/docs/user-guide/rule-engine-2-0/overview/)

---

**Not:** Bu rehber ThingsBoard Community Edition (CE) için hazırlanmıştır. Professional Edition (PE) ek özellikler içerebilir.
