import serial, os
import matplotlib.pyplot as plt
from collections import deque
import csv
import time
import math
import socket

# --- CONFIGURACIÓN ---
PUERTO = 'COM4'
BAUDIOS = 115200
NOMBRE_ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_sensor.csv")

UDP_IP   = "127.0.0.1"
UDP_PORT = 5005

INDICES = {"temp": 0, "hum": 1, "pres": 2, "alt": 3,
           "ax": 4, "ay": 5, "az": 6, "gx": 7, "gy": 8, "gz": 9}

# --- Complementary filter ---
ALPHA = 0.96   # peso del giroscopio (0.96 es típico, ajustable)
roll  = 0.0
pitch = 0.0
yaw   = 0.0
t_prev = None      # para calcular dt real entre paquetes

try:
    ser = serial.Serial(PUERTO, BAUDIOS, timeout=1)
    print(f"Conectado a {PUERTO}.")
except Exception as e:
    print(f"Error de conexión: {e}")
    exit()

# --- Socket UDP para enviar a Processing ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

with open(NOMBRE_ARCHIVO, mode='w', newline='') as f:
    csv.writer(f).writerow([
        "Tiempo_s", "Temperatura", "Humedad", "Presion", "Altitud",
        "Ax", "Ay", "Az", "Gx", "Gy", "Gz",
        "Roll", "Pitch", "Yaw"
    ])

# --- Buffers gráfica ---
max_puntos = 100
t_vals    = deque(maxlen=max_puntos)
temp_vals = deque(maxlen=max_puntos)
hum_vals  = deque(maxlen=max_puntos)
pres_vals = deque(maxlen=max_puntos)
alt_vals  = deque(maxlen=max_puntos)

# --- Figura ---
plt.ion()
fig, (ax0, ax1, ax2, ax3) = plt.subplots(4, 1, figsize=(9, 12))
fig.tight_layout(pad=4.0)

ax0.set_title("Temperatura vs Tiempo"); ax0.set_ylabel("Temperatura (°C)"); ax0.grid(True)
ax1.set_title("Humedad vs Tiempo");     ax1.set_ylabel("Humedad (%)");       ax1.grid(True)
ax2.set_title("Presión vs Tiempo");     ax2.set_ylabel("Presión (hPa)");     ax2.grid(True)
ax3.set_title("Altitud vs Tiempo");     ax3.set_ylabel("Altitud (m)");       ax3.set_xlabel("Tiempo (s)"); ax3.grid(True)

(line0,) = ax0.plot([], [], 'm-o', markersize=3)
(line1,) = ax1.plot([], [], 'b-o', markersize=3)
(line2,) = ax2.plot([], [], 'g-o', markersize=3)
(line3,) = ax3.plot([], [], 'r-o', markersize=3)

t_inicio = time.time()
print(f"Guardando en: {NOMBRE_ARCHIVO} | Ctrl+C para detener")

try:
    while True:
        linea_raw = ser.readline().decode('utf-8', errors='ignore').strip()
        if not linea_raw:
            continue

        partes = linea_raw.split(',')
        if len(partes) < 10:
            continue

        try:
            temp = float(partes[INDICES["temp"]])
            hum  = float(partes[INDICES["hum"]])
            pres = float(partes[INDICES["pres"]])
            alt  = float(partes[INDICES["alt"]])
            ax_  = float(partes[INDICES["ax"]])   # m/s²
            ay_  = float(partes[INDICES["ay"]])   # m/s²
            az_  = float(partes[INDICES["az"]])   # m/s²
            gx_  = float(partes[INDICES["gx"]])   # °/s
            gy_  = float(partes[INDICES["gy"]])   # °/s
            gz_  = float(partes[INDICES["gz"]])   # °/s
        except ValueError:
            continue

        t_ahora = time.time() - t_inicio

        # --- dt real entre paquetes ---
        if t_prev is None:
            dt = 1.0  # primer paquete, asumimos 1s
        else:
            dt = t_ahora - t_prev
        t_prev = t_ahora

        # MPU X apunta al cielo → es nuestro eje vertical
        # MPU Y apunta a la izquierda → es nuestro eje lateral  
        # MPU Z apunta al frente → es nuestro eje longitudinal

        acc_vertical  =  ax_   # cielo
        acc_lateral   = ay_   # izquierda → derecha (negado para que derecha sea positivo)
        acc_frontal   = az_   # frente

        roll_acc  = math.degrees(math.atan2(acc_lateral, acc_vertical))
        pitch_acc = math.degrees(math.atan2(-acc_frontal, math.sqrt(acc_lateral**2 + acc_vertical**2)))

        roll  = roll_acc
        pitch = pitch_acc
        yaw   = 0.0

        # --- CSV ---
        with open(NOMBRE_ARCHIVO, mode='a', newline='') as f:
            csv.writer(f).writerow([
                f"{t_ahora:.2f}", temp, hum, pres, alt,
                ax_, ay_, az_, gx_, gy_, gz_,
                f"{roll:.2f}", f"{pitch:.2f}", f"{yaw:.2f}"
            ])

        # --- UDP a Processing ---
        mensaje = f"{roll:.2f},{pitch:.2f},{yaw:.2f}"
        sock.sendto(mensaje.encode(), (UDP_IP, UDP_PORT))

        # --- Buffers gráfica ---
        t_vals.append(t_ahora)
        temp_vals.append(temp)
        hum_vals.append(hum)
        pres_vals.append(pres)
        alt_vals.append(alt)

        t = list(t_vals)

        line0.set_data(t, list(temp_vals))
        line1.set_data(t, list(hum_vals))
        line2.set_data(t, list(pres_vals))
        line3.set_data(t, list(alt_vals))

        for ax in (ax0, ax1, ax2, ax3):
            ax.relim()
            ax.autoscale_view()

        fig.canvas.draw_idle()
        fig.canvas.flush_events()

        print(
            f"t={t_ahora:.1f}s | "
            f"Temp={temp}°C | Hum={hum}% | Pres={pres}hPa | Alt={alt}m | "
            f"Ac=({ax_},{ay_},{az_}) | Gy=({gx_},{gy_},{gz_}) | "
            f"Roll={roll:.1f}° Pitch={pitch:.1f}° Yaw={yaw:.1f}°"
        )

except KeyboardInterrupt:
    print("\nDetenido. Datos guardados en CSV.")
finally:
    ser.close()
    sock.close()
    plt.ioff()
    plt.show()