from flask import Flask, render_template, request, flash, redirect, url_for
import random
import math
import matplotlib.pyplot as plt
import time
import textwrap
import io
import base64

app = Flask(__name__)
app.secret_key = 'kk'
plt.switch_backend('Agg')



def decode_posisi_ke_rute_manual(posisi):
    posisi_berindeks = list(enumerate(posisi))
    posisi_berindeks.sort(key=lambda x: x[1])
    return [indeks for indeks, nilai in posisi_berindeks]

def hitung_jarak_euclidean(kota1, kota2):
    return math.sqrt((kota1['x'] - kota2['x'])**2 + (kota1['y'] - kota2['y'])**2)

def hitung_total_jarak(rute, daftar_kota):
    total_jarak = 0
    for i in range(len(rute)):
        kota_sekarang_idx = rute[i]
        kota_berikutnya_idx = rute[0] if i == len(rute) - 1 else rute[i+1]
        total_jarak += hitung_jarak_euclidean(daftar_kota[kota_sekarang_idx], daftar_kota[kota_berikutnya_idx])
    return total_jarak

def solve_pso_for_tsp(daftar_kota, n_partikel, max_iter, w, c1, c2, r1, r2):
    n_kota = len(daftar_kota)
    swarm = []; log_inisialisasi = []
    for i in range(n_partikel):
        posisi_awal = [random.random() for _ in range(n_kota)]
        kecepatan_awal = [random.uniform(-0.1, 0.1) for _ in range(n_kota)]
        rute_awal = decode_posisi_ke_rute_manual(posisi_awal)
        fitness_awal = hitung_total_jarak(rute_awal, daftar_kota)
        partikel = {'id': i + 1, 'posisi': posisi_awal, 'kecepatan': kecepatan_awal, 'pbest_posisi': posisi_awal[:], 'pbest_fitness': fitness_awal}
        swarm.append(partikel)
        log_inisialisasi.append({ "id": i + 1, "posisi": posisi_awal, "rute": rute_awal, "fitness": fitness_awal })
        
    gbest_posisi, gbest_fitness = [], float('inf')
    for p in swarm:
        if p['pbest_fitness'] < gbest_fitness: gbest_fitness, gbest_posisi = p['pbest_fitness'], p['pbest_posisi'][:]
    
    log_seluruh_iterasi = []
    for iterasi in range(max_iter):
        log_iterasi_saat_ini = {"iterasi_ke": iterasi + 1, "detail_partikel": [], "gbest_rute": []}
        for p in swarm:
            posisi_sebelum, kecepatan_sebelum, pbest_fitness_sebelum = p['posisi'][:], p['kecepatan'][:], p['pbest_fitness']
            kecepatan_baru, posisi_baru = [], []
            for d in range(n_kota):
                v_baru = (w * kecepatan_sebelum[d]) + (c1 * r1 * (p['pbest_posisi'][d] - posisi_sebelum[d])) + (c2 * r2 * (gbest_posisi[d] - posisi_sebelum[d]))
                kecepatan_baru.append(v_baru)
                x_baru = posisi_sebelum[d] + v_baru
                posisi_baru.append(max(0.0, min(1.0, x_baru)))
            p['kecepatan'], p['posisi'] = kecepatan_baru, posisi_baru
            velocity_delta = [kecepatan_baru[d] - kecepatan_sebelum[d] for d in range(n_kota)]
            position_delta = [posisi_baru[d] - posisi_sebelum[d] for d in range(n_kota)]
            rute_baru = decode_posisi_ke_rute_manual(posisi_baru)
            fitness_baru = hitung_total_jarak(rute_baru, daftar_kota)
            if fitness_baru < pbest_fitness_sebelum: p['pbest_fitness'], p['pbest_posisi'] = fitness_baru, posisi_baru[:]
            log_iterasi_saat_ini["detail_partikel"].append({"id": p['id'], "rute": rute_baru, "fitness": fitness_baru, "velocity_delta": velocity_delta, "position_delta": position_delta, "pbest_fitness_terbaru": p['pbest_fitness']})
        for p in swarm:
            if p['pbest_fitness'] < gbest_fitness: gbest_fitness, gbest_posisi = p['pbest_fitness'], p['pbest_posisi'][:]
        log_iterasi_saat_ini["gbest_fitness"], log_iterasi_saat_ini["gbest_rute"] = gbest_fitness, decode_posisi_ke_rute_manual(gbest_posisi)
        log_seluruh_iterasi.append(log_iterasi_saat_ini)
    return log_inisialisasi, log_seluruh_iterasi



def parse_koordinat(text_area_input):
    daftar_kota = []
    baris = text_area_input.strip().split('\n')
    for idx, line in enumerate(baris):
        line = line.strip()
        if not line: continue
        parts = line.split(',')
        if len(parts) != 3: raise ValueError(f"Format salah pada baris {idx + 1}: '{line}'. Harusnya 'Nama,X,Y'.")
        nama = parts[0].strip()
        if not nama: raise ValueError(f"Nama kota tidak boleh kosong pada baris {idx + 1}.")
        x, y = float(parts[1]), float(parts[2])
        daftar_kota.append({'nama': nama, 'x': x, 'y': y})
    return daftar_kota

def buat_matriks_jarak(daftar_kota):
    n_kota = len(daftar_kota)
    matriks = [[0.0] * n_kota for _ in range(n_kota)]
    for i in range(n_kota):
        for j in range(n_kota):
            jarak = hitung_jarak_euclidean(daftar_kota[i], daftar_kota[j])
            matriks[i][j] = jarak
    return matriks

def buat_plot_base64(daftar_kota, rute, fitness, judul_plot):
    fig, ax = plt.subplots(figsize=(8, 6))
    if rute:
        for i in range(len(rute)):
            kota_awal = daftar_kota[rute[i]]
            kota_akhir = daftar_kota[rute[0] if i == len(rute) - 1 else rute[i+1]]
            ax.plot([kota_awal['x'], kota_akhir['x']], [kota_awal['y'], kota_akhir['y']], 'c-o', markersize=8)
    for kota in daftar_kota:
        ax.plot(kota['x'], kota['y'], 'ro')
        ax.text(kota['x'] + 1, kota['y'] + 1, kota['nama'], fontsize=12, ha='center')
    ax.set_title(f"{judul_plot}\nJarak: {fitness:.2f}", fontsize=14)
    ax.set_xlabel("Koordinat X"); ax.set_ylabel("Koordinat Y"); ax.grid(True)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

def rute_ke_nama(rute_idx, daftar_kota):
    if not rute_idx: return ""
    return " -> ".join([daftar_kota[i]['nama'] for i in rute_idx])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        try:
            params = {'n_partikel': int(request.form['jumlah_partikel']), 'max_iter': int(request.form['jumlah_iterasi']), 'w': float(request.form['w']), 'c1': float(request.form['c1']), 'c2': float(request.form['c2']), 'r1': 0.6, 'r2': 0.5}
            daftar_kota = parse_koordinat(request.form['koordinat_bts'])
            if len(daftar_kota) < 3: raise ValueError("Data lokasi tidak valid atau kurang dari 3 kota.")

            matriks_jarak = buat_matriks_jarak(daftar_kota)

            start_time = time.time()
            log_awal, log_iterasi_hasil = solve_pso_for_tsp(daftar_kota, **params)
            waktu_komputasi = time.time() - start_time
            
            hasil_untuk_template = {
                "parameter_input": params, "waktu_komputasi": waktu_komputasi, 
                "daftar_kota_awal": daftar_kota, "laporan_iterasi": [],
                "matriks_jarak": matriks_jarak
            }

            for p in log_awal:
                p['rute_nama'] = rute_ke_nama(p['rute'], daftar_kota)
            gbest_fitness_awal = min(p['fitness'] for p in log_awal)
            gbest_rute_awal = next((p['rute'] for p in log_awal if p['fitness'] == gbest_fitness_awal), [])
            plot_awal = buat_plot_base64(daftar_kota, gbest_rute_awal, gbest_fitness_awal, "Rute gBest Awal (Iterasi 0)")
            hasil_untuk_template['laporan_iterasi'].append({"judul": "ANALISIS KONDISI AWAL (ITERASI 0)", "data_tabel": log_awal, "plot_base64": plot_awal, "tipe": "awal", "gbest_rute": gbest_rute_awal, "gbest_rute_nama": rute_ke_nama(gbest_rute_awal, daftar_kota)})
            
            for log_iter in log_iterasi_hasil:
                iterasi_ke = log_iter['iterasi_ke']
                for detail_partikel in log_iter['detail_partikel']:
                    detail_partikel['rute_nama'] = rute_ke_nama(detail_partikel['rute'], daftar_kota)
                plot_iter = buat_plot_base64(daftar_kota, log_iter['gbest_rute'], log_iter['gbest_fitness'], f"Rute gBest Setelah Iterasi ke-{iterasi_ke}")
                log_iter['plot_base64'] = plot_iter
                log_iter['tipe'] = 'lanjutan'
                log_iter['judul'] = f"ANALISIS SETELAH UPDATE PADA ITERASI KE-{iterasi_ke}"
                log_iter['gbest_rute_nama'] = rute_ke_nama(log_iter['gbest_rute'], daftar_kota)
                hasil_untuk_template['laporan_iterasi'].append(log_iter)
            
            return render_template('hasil.html', hasil=hasil_untuk_template)
        except ValueError as e:
            flash(f"Input Error: {e}")
            return redirect(url_for('index'))
        except Exception as e:
            flash(f"Terjadi kesalahan internal: {e}")
            return redirect(url_for('index'))


@app.route('/lihat-kode')
def lihat_kode():
    """Route ini membaca file app.py dan menampilkannya di halaman baru."""
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            kode_sumber = f.read()
        return render_template('script_code.html', kode_sumber=kode_sumber)
    except Exception as e:
        return f"Gagal membaca file kode: {e}"


if __name__ == '__main__':
    app.run(debug=True)