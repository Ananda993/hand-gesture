import cv2
import mediapipe as mp
import random
import math
import numpy as np
import time

# --- Persiapan Awal ---
# Siapkan library MediaPipe untuk mendeteksi tangan di kamera.
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Nyalakan webcam. Angka 1 mungkin perlu diganti 0 jika webcam eksternal tidak terdeteksi.
cap = cv2.VideoCapture(1)

# Kalau webcamnya tidak bisa nyala, hentikan program.
if not cap.isOpened():
    print("Error: Tidak bisa membuka kamera.")
    exit()

# Ambil satu gambar dari webcam untuk tahu ukuran layarnya.
ret, frame = cap.read()
if not ret:
    print("Error: Tidak bisa membaca frame dari kamera.")
    exit()
FRAME_HEIGHT, FRAME_WIDTH, _ = frame.shape


# --- Blueprint untuk Objek-Objek di Game ---

class Player:
    """Blueprint untuk membuat pesawat pemain."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.smoothing = 0.2 # Angka ini membuat pergerakan pesawat lebih mulus, tidak kaku.
        self.radius = 25
        self.color = (255, 255, 0)  # Warna Cyan (biru muda)
        self.health = 100
        self.damage = 10  # Kekuatan tembakan awal
        self.shoot_cooldown = 0
        self.max_cooldown = 5 # Jeda antar tembakan (dalam frame) agar tidak menembak terus-menerus.

    def set_target(self, x, y):
        # Fungsi ini untuk menentukan posisi tujuan pesawat (mengikuti tangan).
        self.target_x = x
        self.target_y = y

    def draw(self, image):
        # Biar lebih keren, pesawatnya kita gambar dalam bentuk segitiga.
        pts = np.array([
            [self.x, self.y - self.radius],
            [self.x - self.radius * 0.8, self.y + self.radius * 0.8],
            [self.x + self.radius * 0.8, self.y + self.radius * 0.8]
        ], np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.fillPoly(image, [pts], self.color)
        cv2.polylines(image, [pts], isClosed=True, color=(255, 100, 0), thickness=2)

    def update(self):
        # Gerakkan pesawat secara perlahan ke posisi target (tangan).
        self.x += (self.target_x - self.x) * self.smoothing
        self.y += (self.target_y - self.y) * self.smoothing
        
        # Setiap frame, kurangi waktu jeda tembakan.
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def shoot(self):
        # Pesawat baru bisa menembak lagi kalau waktu jedanya sudah nol.
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.max_cooldown
            # Peluru akan muncul dari depan pesawat dan bergerak ke atas.
            return Projectile(self.x, self.y - self.radius)
        return None

class Projectile:
    """Blueprint untuk peluru yang ditembakkan pemain."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 8
        self.color = (0, 255, 255)  # Warna kuning untuk peluru
        self.speed = 25

    def draw(self, image):
        cv2.circle(image, (int(self.x), int(self.y)), self.radius, self.color, -1)

    def update(self):
        # Fungsi ini membuat peluru terus bergerak ke atas layar.
        self.y -= self.speed

class Enemy:
    """Blueprint untuk pesawat musuh."""
    def __init__(self):
        self.radius = random.randint(15, 35)
        self.x = random.randint(self.radius, FRAME_WIDTH - self.radius)
        self.y = -self.radius # Musuh muncul dari atas layar, jadi awalnya posisinya negatif.
        # Biar lebih menantang, nyawa musuh akan semakin besar seiring permainan.
        possible_healths = [10, 15, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        max_index = min(len(possible_healths) - 1, kills // 2)
        self.max_health = random.choice(possible_healths[:max_index + 2])
        self.health = self.max_health
        self.speed = random.randint(2, 5)
        self.color = (random.randint(100,255), random.randint(0,100), random.randint(100,255)) # Setiap musuh warnanya acak.

    def draw(self, image):
        # Gambar musuh sebagai lingkaran.
        cv2.circle(image, (int(self.x), int(self.y)), self.radius, self.color, -1)
        # Tampilkan bar nyawa di atas musuh jika dia sudah tertembak.
        if self.health < self.max_health:
            health_ratio = self.health / self.max_health
            bar_width = self.radius * 2
            bar_height = 7
            cv2.rectangle(image, (int(self.x - self.radius), int(self.y - self.radius - bar_height - 5)),
                          (int(self.x + self.radius), int(self.y - self.radius - 5)), (0, 0, 150), -1)
            cv2.rectangle(image, (int(self.x - self.radius), int(self.y - self.radius - bar_height - 5)),
                          (int(self.x - self.radius + bar_width * health_ratio), int(self.y - self.radius - 5)), (0, 255, 0), -1)

    def update(self):
        # Musuh hanya bergerak lurus ke bawah.
        self.y += self.speed

class Particle:
    """Blueprint untuk partikel kecil yang muncul saat ada ledakan."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = random.randint(2, 5)
        self.color = random.choice([(0,165,255), (0,255,255), (255,255,255)]) # Warnanya seperti api: oranye, kuning, putih.
        self.life = 20 # Partikel akan hilang setelah beberapa frame.
        self.vx = random.uniform(-5, 5) # Kecepatan horizontal acak.
        self.vy = random.uniform(-5, 5) # Kecepatan vertikal acak.

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.radius *= 0.95 # Partikelnya akan makin mengecil.

    def draw(self, image):
        cv2.circle(image, (int(self.x), int(self.y)), int(self.radius), self.color, -1)

class PowerUp:
    """Blueprint untuk item bantuan (power-up) yang bisa diambil pemain."""
    def __init__(self, x, y, type='health'):
        self.x = x
        self.y = y
        self.type = type
        self.radius = 15
        self.speed = 3

    def update(self):
        # Power-up bergerak ke bawah, sama seperti musuh.
        self.y += self.speed

    def draw(self, image):
        # Untuk power-up nyawa, kita gambar simbol '+' di dalam lingkaran hijau.
        cv2.putText(image, "+", (int(self.x) - 10, int(self.y) + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(image, (int(self.x), int(self.y)), self.radius, (0, 255, 0), 2)


class Star:
    """Blueprint untuk bintang-bintang di latar belakang agar terlihat seperti luar angkasa."""
    def __init__(self):
        self.x = random.randint(0, FRAME_WIDTH)
        self.y = random.randint(0, FRAME_HEIGHT)
        self.radius = random.randint(1, 2)
        self.speed = random.uniform(0.5, 1.5)

    def update(self):
        # Bintang bergerak ke bawah.
        self.y += self.speed
        # Jika sudah sampai bawah, pindahkan lagi ke atas dengan posisi acak.
        if self.y > FRAME_HEIGHT:
            self.y = 0
            self.x = random.randint(0, FRAME_WIDTH)
    
    def draw(self, image):
        cv2.circle(image, (int(self.x), int(self.y)), self.radius, (200, 200, 200), -1)

# --- Variabel-Variabel Penting untuk Game ---
player = Player(FRAME_WIDTH // 2, FRAME_HEIGHT - 100)
projectiles = []
enemies = []
particles = []
powerups = []
stars = [Star() for _ in range(100)] # Buat 100 bintang untuk latar belakang.
kills = 0
# Variabel ini mengontrol kondisi game: di menu awal, sedang main, atau sudah kalah.
game_state = 'START_SCREEN' 
last_spawn_time = time.time() # Mencatat waktu terakhir musuh muncul.
spawn_interval = 2.0 # Jeda waktu antar kemunculan musuh (dalam detik).

# --- Fungsi-Fungsi Pembantu ---
def create_explosion(x, y, count=20):
    # Fungsi ini untuk memunculkan banyak partikel sekaligus saat ada ledakan.
    for _ in range(count):
        particles.append(Particle(x, y))

def draw_ui(image):
    # Fungsi ini untuk menampilkan info seperti nyawa, damage, dan skor di bagian atas layar.
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (FRAME_WIDTH, 50), (0, 0, 0), -1)
    alpha = 0.6
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    
    health_text = f"NYAWA: {player.health}"
    damage_text = f"DAMAGE: {player.damage:.1f}"
    kills_text = f"KILLS: {kills}"
    
    cv2.putText(image, health_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(image, damage_text, (FRAME_WIDTH // 2 - 100, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(image, kills_text, (FRAME_WIDTH - 200, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return image
    
def display_game_over(image):
    # Fungsi ini untuk menampilkan layar "GAME OVER" saat pemain kalah.
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0), -1)
    alpha = 0.7
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    text1, text2, text3, text4 = "GAME OVER", f"Total Kills: {kills}", "Tekan 'R' untuk Mulai Lagi", "Tekan 'Q' untuk Keluar"
    (w1, h1), _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_TRIPLEX, 3, 3)
    (w2, h2), _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 2)
    (w3, h3), _ = cv2.getTextSize(text3, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    (w4, h4), _ = cv2.getTextSize(text4, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    cv2.putText(image, text1, ((FRAME_WIDTH - w1) // 2, FRAME_HEIGHT // 2 - h1), cv2.FONT_HERSHEY_TRIPLEX, 3, (0, 0, 255), 3)
    cv2.putText(image, text2, ((FRAME_WIDTH - w2) // 2, FRAME_HEIGHT // 2 + h2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(image, text3, ((FRAME_WIDTH - w3) // 2, FRAME_HEIGHT // 2 + h2 + h3 + 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(image, text4, ((FRAME_WIDTH - w4) // 2, FRAME_HEIGHT // 2 + h2 + h3 + h4 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return image

def display_start_screen(image):
    # Fungsi ini untuk menampilkan menu awal permainan.
    overlay = image.copy()
    cv2.rectangle(overlay, (0, 0), (FRAME_WIDTH, FRAME_HEIGHT), (0, 0, 0), -1)
    alpha = 0.7
    image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
    text1 = "Game Pesawat Tangan"
    text2 = "Tunjukkan Tangan Anda ke Kamera"
    text3 = "Untuk Memulai"
    (w1, h1), _ = cv2.getTextSize(text1, cv2.FONT_HERSHEY_TRIPLEX, 2, 3)
    (w2, h2), _ = cv2.getTextSize(text2, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    (w3, h3), _ = cv2.getTextSize(text3, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)
    cv2.putText(image, text1, ((FRAME_WIDTH - w1) // 2, FRAME_HEIGHT // 2 - h1), cv2.FONT_HERSHEY_TRIPLEX, 2, (0, 255, 255), 3)
    cv2.putText(image, text2, ((FRAME_WIDTH - w2) // 2, FRAME_HEIGHT // 2 + h2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(image, text3, ((FRAME_WIDTH - w3) // 2, FRAME_HEIGHT // 2 + h2 + h3 + 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    return image

def reset_game():
    # Fungsi ini dipanggil saat pemain menekan 'R' setelah kalah untuk mengulang permainan.
    global player, projectiles, enemies, particles, powerups, kills, game_state, last_spawn_time, spawn_interval
    player = Player(FRAME_WIDTH // 2, FRAME_HEIGHT - 100)
    projectiles, enemies, particles, powerups = [], [], [], []
    kills = 0
    game_state = 'PLAYING'
    last_spawn_time = time.time()
    spawn_interval = 2.0

# --- Loop Utama Game (Semua Aksi Terjadi di Sini) ---
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    # Balik gambar secara horizontal agar seperti cermin.
    frame = cv2.flip(frame, 1)

    # Warna gambar dari webcam itu BGR, tapi MediaPipe butuhnya RGB, jadi kita ubah dulu.
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    hand_detected = results.multi_hand_landmarks is not None
    
    # Siapkan layar hitam untuk menggambar bintang-bintang.
    star_canvas = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
    star_canvas[:] = (20, 10, 0) # Warna biru tua gelap.

    # Gerakkan dan gambar semua bintang di layar khusus bintang.
    for s in stars:
        s.update()
        s.draw(star_canvas)

    # Gabungkan gambar dari webcam dengan latar bintang.
    # Gambar webcamnya dibuat agak transparan biar bintang-bintangnya tetap kelihatan.
    game_surface = cv2.addWeighted(frame, 0.4, star_canvas, 0.6, 0)

    if game_state == 'START_SCREEN':
        game_surface = display_start_screen(game_surface)
        # Jika tangan terdeteksi di menu awal, langsung mulai permainan.
        if hand_detected:
            for hand_landmarks in results.multi_hand_landmarks:
                 mp_drawing.draw_landmarks(game_surface, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            game_state = 'PLAYING'
            last_spawn_time = time.time() # Atur ulang timer kemunculan musuh.

    elif game_state == 'PLAYING':
        # Kalau kamera berhasil mendeteksi tangan, jalankan kode di dalam sini.
        if hand_detected:
            for hand_landmarks in results.multi_hand_landmarks:
                # Kita pakai posisi ujung jari telunjuk (landmark no. 8) untuk mengontrol pesawat.
                landmark = hand_landmarks.landmark[8] 
                player.set_target(int(landmark.x * FRAME_WIDTH), int(landmark.y * FRAME_HEIGHT))
                # Tembakkan peluru.
                new_projectile = player.shoot()
                if new_projectile: projectiles.append(new_projectile)

                # Biar keren, kita gambar juga kerangka tangan yang terdeteksi.
                mp_drawing.draw_landmarks(game_surface, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        player.update()

        # Munculkan musuh baru secara berkala.
        if time.time() - last_spawn_time > spawn_interval:
            enemies.append(Enemy())
            last_spawn_time = time.time()
            # Seiring waktu, musuh akan muncul lebih cepat.
            spawn_interval = max(0.5, spawn_interval * 0.99)

        # Update dan gambar semua peluru.
        for p in list(projectiles):
            p.update()
            p.draw(game_surface)
            if p.y < 0: projectiles.remove(p) # Hapus peluru yang keluar layar.
        
        # Lakukan update untuk setiap musuh di layar.
        for e in list(enemies):
            e.update()
            e.draw(game_surface)
            
            # Cek apakah ada peluru yang kena musuh.
            for p in list(projectiles):
                if math.sqrt((e.x - p.x)**2 + (e.y - p.y)**2) < e.radius + p.radius:
                    e.health -= player.damage
                    projectiles.remove(p)
                    break
            
            # Jika nyawa musuh habis.
            if e.health <= 0:
                kills += 1
                player.damage += 1.5 # Setiap bunuh musuh, damage pemain bertambah.
                create_explosion(e.x, e.y) # Buat efek ledakan.
                if random.random() < 0.15: # 15% kemungkinan musuh menjatuhkan power-up.
                    powerups.append(PowerUp(e.x, e.y))
                enemies.remove(e)
                continue

            # Cek apakah musuh menabrak pesawat pemain.
            if math.sqrt((e.x - player.x)**2 + (e.y - player.y)**2) < e.radius + player.radius:
                player.health -= int(e.max_health / 2) # Nyawa berkurang setengah dari max nyawa musuh.
                create_explosion(e.x, e.y)
                enemies.remove(e)
                continue
            
            # Kalau musuh berhasil lolos sampai ke bawah layar, nyawa pemain berkurang.
            if e.y > FRAME_HEIGHT + e.radius:
                player.health -= 10
                enemies.remove(e)

        player.draw(game_surface)
        
        # Update dan cek power-up.
        for pw in list(powerups):
            pw.update()
            pw.draw(game_surface)
            # Cek jika pemain mengambil power-up.
            if math.sqrt((pw.x - player.x)**2 + (pw.y - player.y)**2) < pw.radius + player.radius:
                if pw.type == 'health': player.health = min(100, player.health + 25) # Tambah nyawa, maksimal 100.
                powerups.remove(pw)
            elif pw.y > FRAME_HEIGHT: powerups.remove(pw) # Hapus power-up yang lolos.

        # Update dan gambar partikel ledakan.
        for p in list(particles):
            p.update()
            p.draw(game_surface)
            if p.life <= 0: particles.remove(p) # Hapus partikel jika sudah 'mati'.

        # Jika nyawa pemain habis, game over.
        if player.health <= 0:
            player.health = 0
            game_state = 'GAME_OVER'
    
    # Tampilkan UI di atas semua elemen game.
    game_surface = draw_ui(game_surface)

    # Jika kondisi game adalah GAME_OVER, tampilkan layarnya.
    if game_state == 'GAME_OVER':
        game_surface = display_game_over(game_surface)

    # Tampilkan hasil akhir gambar ke jendela.
    cv2.imshow('Game Pesawat Tangan', game_surface)

    # Cek input keyboard.
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): break # Tekan 'q' untuk keluar.
    if game_state == 'GAME_OVER' and key == ord('r'): reset_game() # Tekan 'r' untuk main lagi.

# --- Selesai ---
# Matikan webcam dan tutup semua jendela.
cap.release()
cv2.destroyAllWindows()
