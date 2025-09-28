# 🎮 Game Pesawat Tangan (OpenCV + MediaPipe)

Game ini dibuat dengan **Python + OpenCV + MediaPipe** untuk mendeteksi tangan sebagai kontrol pesawat. Pemain menggerakkan pesawat menggunakan jari telunjuk, menembak musuh secara otomatis, dan berusaha bertahan selama mungkin. Efek ledakan, power-up, serta latar bintang ditambahkan untuk membuat permainan lebih seru.

---

## 🚀 Persiapan Lingkungan

1. **Install Python 3.11**
   Unduh di [python.org](https://www.python.org/downloads/windows/) dan saat instalasi centang opsi **Add Python to PATH**.
   Cek instalasi:

   ```bash
   python --version
   ```

2. **Buat Virtual Environment**

   ```bash
   python -m venv venv
   ```

   Aktifkan:

   * CMD:

     ```bash
     venv\Scripts\activate
     ```
   * PowerShell:

     ```bash
     .\venv\Scripts\Activate
     ```

3. **Install Dependency**

   ```bash
   pip install --upgrade pip
   pip install opencv-python mediapipe numpy
   ```

---

## 📷 Pengaturan Kamera

* Default menggunakan webcam bawaan laptop:

  ```python
  cap = cv2.VideoCapture(0)
  ```
* Jika ingin kualitas lebih baik, gunakan aplikasi **iRIUM Webcam** di HP:

  * Install driver iRIUM di PC dan app di HP.
  * Hubungkan lewat USB/WiFi.
  * Ubah index kamera di kode menjadi `1`:

    ```python
    cap = cv2.VideoCapture(1)
    ```

---

## ▶️ Cara Menjalankan Game

Aktifkan virtual environment lalu jalankan:

```bash
python main.py
```

**Kontrol:**

* Gerakkan jari telunjuk di depan kamera → pesawat mengikuti.
* Peluru ditembak otomatis.
* Tekan `Q` → keluar dari game.
* Tekan `R` → restart setelah Game Over.

---

## 🛠️ Catatan

* **Mediapipe belum support Python 3.13**, gunakan Python 3.11.
* Jika kamera tidak terbuka, coba ubah index `0`, `1`, atau `2` di `cv2.VideoCapture()`.
* Bisa tambahkan screenshot atau GIF gameplay di bagian preview.

---

## 📸 Preview

*(Tambahkan screenshot/gif hasil game di sini jika t
