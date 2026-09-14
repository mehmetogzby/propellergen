import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def naca4(number, n=60):
    m = int(number[0]) / 100.0
    p = int(number[1]) / 10.0
    t = int(number[2:]) / 100.0
    
    beta = np.linspace(0, np.pi, n)
    x = 0.5 * (1 - np.cos(beta))
    
    yc = np.zeros_like(x)
    dyc_dx = np.zeros_like(x)
    for i, xi in enumerate(x):
        if xi < p:
            yc[i] = (m / (p**2 + 1e-9)) * (2 * p * xi - xi**2)
            dyc_dx[i] = (2 * m / (p**2 + 1e-9)) * (p - xi)
        else:
            yc[i] = (m / ((1 - p)**2 + 1e-9)) * ((1 - 2 * p) + 2 * p * xi - xi**2)
            dyc_dx[i] = (2 * m / ((1 - p)**2 + 1e-9)) * (p - xi)
            
    yt = 5 * t * (0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2 + 0.2843 * x**3 - 0.1015 * x**4)
    
    theta = np.arctan(dyc_dx)
    xu = x - yt * np.sin(theta)
    yu = yc + yt * np.cos(theta)
    xl = x + yt * np.sin(theta)
    yl = yc - yt * np.cos(theta)
    
    X = np.concatenate((xu[::-1], xl[1:]))
    Y = np.concatenate((yu[::-1], yl[1:]))
    
    return X, Y

class PropellerGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PropellerGen")
        
        # Windows Görev Çubuğu (Taskbar) simgesi için zorunlu ctypes ayarı
        try:
            import ctypes
            myappid = 'degz.propellergen.v2' # Arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
            
        try:
            self.root.iconbitmap(resource_path("propeller_icon_v2.ico"))
        except:
            pass
            
        self.root.geometry("1400x850")
        
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        elif 'winnative' in style.theme_names():
            style.theme_use('winnative')
        else:
            style.theme_use('classic')
            
        style.configure(".", font=("Tahoma", 9))
        
        left_panel = ttk.Frame(root, width=450, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Button(left_panel, text="OpenProp Çıktısı (.txt) Yükle", command=self.load_openprop_file).pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_file = ttk.Label(left_panel, text="Yüklü Dosya: Yok")
        self.lbl_file.pack(pady=2, anchor=tk.W)
        self.lbl_perf = ttk.Label(left_panel, text="Performans: Bekleniyor...")
        self.lbl_perf.pack(pady=2, anchor=tk.W)
        
        ttk.Label(left_panel, text="Çıktı Ayarları", font=("Tahoma", 10, "bold")).pack(pady=(15, 5), anchor=tk.W)
        
        self.vars = {}
        def add_input(label, default_val):
            f = ttk.Frame(left_panel)
            f.pack(fill=tk.X, pady=2)
            ttk.Label(f, text=label, width=28).pack(side=tk.LEFT)
            var = tk.DoubleVar(value=default_val)
            ttk.Entry(f, textvariable=var, width=10).pack(side=tk.RIGHT)
            self.vars[label] = var
            
        add_input("Pervane Dış Çapı [mm]", 76.0) 
        add_input("Hub Çapı [mm]", 30.0) 
        add_input("Hub Uzunluğu [mm]", 41.0)     
        add_input("Hatve Ekseni Konumu (0-1)", 0.5) 
        add_input("Hatve Ekle (Derece)", 0.0) 
        add_input("Maksimum Skew (Derece)", 5.0) 
        add_input("Mesh Çözünürlüğü (20-60)", 25.0)
        
        self.vars["Kanat Sayısı"] = tk.IntVar(value=3)  
        f_b = ttk.Frame(left_panel)
        f_b.pack(fill=tk.X, pady=2)
        ttk.Label(f_b, text="Kanat Sayısı", width=28).pack(side=tk.LEFT)
        ttk.Entry(f_b, textvariable=self.vars["Kanat Sayısı"], width=10).pack(side=tk.RIGHT)
        
        add_input("NACA Profili", 2412)
        
        ttk.Button(left_panel, text="Geometriyi Güncelle ve Çiz", command=self.generate_and_plot).pack(fill=tk.X, pady=(20, 5))
        
        ttk.Label(left_panel, text="--- Çıktı Alma ---").pack(pady=(5, 2))
        f_export = ttk.Frame(left_panel)
        f_export.pack(fill=tk.X)
        ttk.Button(f_export, text="STL Çıktısı Al", command=lambda: self.export_mesh('stl')).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(f_export, text="OBJ Çıktısı Al", command=lambda: self.export_mesh('obj')).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        ttk.Button(left_panel, text="Verim Hesaplayıcı", command=self.open_cfd_calculator).pack(fill=tk.X, pady=(15, 5))
        
        self.log = tk.Text(left_panel, height=14, bg="white", fg="black", font=("Courier New", 9), relief=tk.SUNKEN, borderwidth=2)
        self.log.pack(fill=tk.BOTH, expand=True, pady=10)
        
        viz_frame = ttk.Frame(root, relief=tk.SUNKEN, borderwidth=2)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.fig = plt.Figure(figsize=(8, 8), dpi=100)
        self.fig.patch.set_facecolor('#F0F0F0') 
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#F0F0F0') 
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        self.ax.xaxis.pane.set_edgecolor('#DDDDDD')
        self.ax.yaxis.pane.set_edgecolor('#DDDDDD')
        self.ax.zaxis.pane.set_edgecolor('#DDDDDD')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.mesh_faces = []
        self.mesh_vertices = []
        self.current_data = None 
        
        self.base_eff = 0
        self.base_kt = 0
        self.base_kq = 0
        self.base_J = 0
        self.base_IT = 0
        self.base_IQ = 0
        
        self.log.insert(tk.END, "PropellerGen Başlatıldı.\n")

    def calc_integrals(self, Z, max_skew_deg, pitch_add_deg):
        r_R_list, c_D_list, pitch_list = self.current_data
        J = self.base_J
        if J <= 0: return 0, 0
        
        IT = 0.0
        IQ = 0.0
        r_root = r_R_list[0]
        
        for i, x in enumerate(r_R_list):
            if x < 0.05: continue
            
            c_D = c_D_list[i]
            beta_deg = pitch_list[i] + pitch_add_deg
            beta_rad = math.radians(beta_deg)
            
            phi_rad = math.atan(J / (math.pi * x))
            
            skew_deg = 0
            if x > r_root:
                skew_deg = max_skew_deg * (((x - r_root) / (1.0 - r_root)) ** 2)
            skew_rad = math.radians(skew_deg)
            
            alpha = beta_rad - phi_rad
            sweep_factor = math.cos(skew_rad)
            
            dx = 0
            if i < len(r_R_list) - 1:
                dx = r_R_list[i+1] - r_R_list[i]
            else:
                dx = r_R_list[i] - r_R_list[i-1]
                
            dIT = c_D * (x**2) * alpha * sweep_factor * dx
            dIQ = c_D * (x**3) * alpha * (sweep_factor**0.8) * dx
            
            IT += dIT
            IQ += dIQ
            
        interference_T = 1.0
        interference_Q = 1.0
        if hasattr(self, 'base_Z') and self.base_Z > 0:
            Z_diff = float(Z) - self.base_Z
            interference_T = 0.94 ** Z_diff  # Thrust loss per extra blade (cascade effect)
            interference_Q = 0.98 ** Z_diff  # Torque loss per extra blade
            
        return IT * Z * interference_T, IQ * Z * interference_Q

    def open_cfd_calculator(self):
        calc_win = tk.Toplevel(self.root)
        calc_win.title("Verim Hesaplayıcı")
        calc_win.geometry("400x450")
        calc_win.configure(padx=10, pady=10)
        
        ttk.Label(calc_win, text="StarCCM+ / SolidWorks CFD Sonuçlarınızı Girin:", font=("Arial", 10, "bold")).pack(pady=(0,10))
        
        vars_cfd = {}
        def add_field(label, default_val):
            frame = ttk.Frame(calc_win)
            frame.pack(fill=tk.X, pady=3)
            ttk.Label(frame, text=label, width=22).pack(side=tk.LEFT)
            v = tk.StringVar(value=str(default_val))
            vars_cfd[label] = v
            ttk.Entry(frame, textvariable=v, width=15).pack(side=tk.RIGHT)
            
        D_default = self.vars["Pervane Dış Çapı [mm]"].get() / 1000.0 if "Pervane Dış Çapı [mm]" in self.vars else 0.076
        
        add_field("İlerleme Hızı (m/s)", "1.0")
        add_field("Pervane Devri (RPM)", "3000")
        add_field("İtme Kuvveti T (Newton)", "15.0")
        add_field("Tork Q (N.m)", "0.12")
        add_field("Su Yoğunluğu (kg/m³)", "998.0")
        add_field("Pervane Çapı (m)", str(D_default))
        
        lbl_res = ttk.Label(calc_win, text="Sonuçlar burada görünecek...", foreground="blue", font=("Arial", 11, "bold"), justify=tk.LEFT)
        
        def calculate_efficiency():
            try:
                Va = float(vars_cfd["İlerleme Hızı (m/s)"].get())
                RPM = float(vars_cfd["Pervane Devri (RPM)"].get())
                T = float(vars_cfd["İtme Kuvveti T (Newton)"].get())
                Q = float(vars_cfd["Tork Q (N.m)"].get())
                rho = float(vars_cfd["Su Yoğunluğu (kg/m³)"].get())
                D = float(vars_cfd["Pervane Çapı (m)"].get())
                
                n = RPM / 60.0
                if n == 0 or D == 0:
                    lbl_res.config(text="Hata: RPM veya Çap 0 olamaz!")
                    return
                
                J = Va / (n * D)
                Kt = T / (rho * (n**2) * (D**4))
                Kq = Q / (rho * (n**2) * (D**5))
                
                if Kq == 0:
                    eff = 0
                else:
                    eff = (J / (2 * math.pi)) * (Kt / Kq)
                
                eff_pct = eff * 100.0
                Power = 2 * math.pi * n * Q
                
                res_text = (f"J (İlerleme Oranı): {J:.4f}\n"
                            f"Kt (İtme Katsayısı): {Kt:.4f}\n"
                            f"Kq (Tork Katsayısı): {Kq:.4f}\n\n"
                            f"Mekanik Güç: {Power:.2f} Watt\n"
                            f"GERÇEK VERİM: %{eff_pct:.2f}")
                lbl_res.config(text=res_text, foreground="green")
            except Exception as e:
                lbl_res.config(text=f"Hata: {e}", foreground="red")
                
        ttk.Button(calc_win, text="Hesapla", command=calculate_efficiency).pack(pady=15)
        lbl_res.pack(pady=10, fill=tk.BOTH, expand=True)

    def load_openprop_file(self):
        filepath = filedialog.askopenfilename(title="OpenProp Çıktısını Seçin", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not filepath: return
        try:
            filename = os.path.basename(filepath)
            self.lbl_file.config(text=f"Yüklü Dosya: {filename}")
            self.log.insert(tk.END, f"\nOkunuyor: {filename}...\n")
            
            with open(filepath, 'r') as f: lines = f.readlines()
                
            eff, kt, kq = "N/A", "N/A", "N/A"
            header_idx = -1
            r_idx, c_idx, b_idx = -1, -1, -1
            
            for i, line in enumerate(lines):
                if "Eff" in line and "=" in line: eff = line.split("=")[1].strip()
                elif "Kt" in line and "=" in line: kt = line.split("=")[1].strip()
                elif "Kq" in line and "=" in line: kq = line.split("=")[1].strip()
                    
                if "r/R" in line and "c/D" in line:
                    header_idx = i
                    headers = line.strip().split()
                    r_idx = headers.index("r/R")
                    c_idx = headers.index("c/D")
                    b_idx = headers.index("BetaI") if "BetaI" in headers else headers.index("Beta")
                    break
                    
            if header_idx == -1: raise ValueError("OpenProp çıktı tablosu bulunamadı!")
                
            r_R_list, c_D_list, pitch_list = [], [], []
            for line in lines[header_idx+1:]:
                parts = line.strip().split()
                if len(parts) == 0: continue 
                if len(parts) > max(r_idx, c_idx, b_idx):
                    try:
                        r_R_list.append(float(parts[r_idx]))
                        c_D_list.append(float(parts[c_idx]))
                        pitch_list.append(float(parts[b_idx]))
                    except ValueError: break 
                        
            if len(r_R_list) < 2: raise ValueError("Yeterli kesit verisi okunamadı!")
                
            r_arr = np.array(r_R_list)
            c_arr = np.array(c_D_list)
            p_arr = np.array(pitch_list)
            
            fixed = False
            if c_arr[0] < 0.05:
                c_arr[0] = c_arr[1] * 0.9
                fixed = True
            if c_arr[-1] < 0.01:
                c_arr[-1] = c_arr[-2] * 0.4
                fixed = True
            if p_arr[0] < 1.0:
                p_arr[0] = p_arr[1] * 1.05
                fixed = True
                
            if fixed:
                self.log.insert(tk.END, "Uyarı: Auto-Fix uygulandı (Sıfır kord düzeltmesi).\n")
                
            self.current_data = (r_arr, c_arr, p_arr)
            
            try:
                self.base_eff = float(eff)
                self.base_kt = float(kt)
                self.base_kq = float(kq)
                self.base_J = self.base_eff * 2 * math.pi * self.base_kq / self.base_kt
                
                # Default OpenProp skew=0, pitch_add=0
                self.base_Z = float(self.vars["Kanat Sayısı"].get())
                self.base_IT, self.base_IQ = self.calc_integrals(self.base_Z, 0.0, 0.0)
                
                self.lbl_perf.config(text=f"Performans: Verim(Eff)=%{self.base_eff*100:.1f} | Kt={self.base_kt:.4f} | Kq={self.base_kq:.4f}")
            except Exception as pe:
                self.log.insert(tk.END, f"Performans parse hatası: {pe}\n")
            
            self.log.insert(tk.END, f"Başarılı! {len(r_arr)} adet kesit okundu.\n")
            self.generate_and_plot()
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunurken bir hata oluştu:\n{e}")

    def update_performance_label(self):
        if self.current_data is None or self.base_J <= 0 or self.base_IT <= 0: return
        
        Z = self.vars["Kanat Sayısı"].get()
        skew = self.vars["Maksimum Skew (Derece)"].get()
        pitch_add = self.vars["Hatve Ekle (Derece)"].get()
        
        new_IT, new_IQ = self.calc_integrals(Z, skew, pitch_add)
        
        if new_IT > 0 and new_IQ > 0:
            new_Kt = self.base_kt * (new_IT / self.base_IT)
            new_Kq = self.base_kq * (new_IQ / self.base_IQ)
            new_Eff = (self.base_J / (2 * math.pi)) * (new_Kt / new_Kq) if new_Kq > 0 else 0
            self.lbl_perf.config(text=f"Performans: Verim(Eff)=%{new_Eff*100:.1f} | Kt={new_Kt:.4f} | Kq={new_Kq:.4f}")

    def generate_geometry(self):
        if self.current_data is None: return False
        r_R_list, c_D_list, pitch_list = self.current_data
        
        D_prop = self.vars["Pervane Dış Çapı [mm]"].get()
        D_hub = self.vars["Hub Çapı [mm]"].get()
        L_hub = self.vars["Hub Uzunluğu [mm]"].get()
        N_blades = self.vars["Kanat Sayısı"].get()
        pitch_axis = self.vars["Hatve Ekseni Konumu (0-1)"].get()
        max_skew_deg = self.vars["Maksimum Skew (Derece)"].get()
        pitch_add_deg = self.vars["Hatve Ekle (Derece)"].get()
        naca_str = str(int(self.vars["NACA Profili"].get())).zfill(4)
        
        N_airfoil = int(self.vars["Mesh Çözünürlüğü (20-60)"].get())
        
        R_prop = D_prop / 2.0
        R_hub = D_hub / 2.0
        
        r_stations = r_R_list * R_prop
        chord_dist = c_D_list * D_prop
        theta_dist = np.radians(pitch_list + pitch_add_deg) 
        
        # Hub içine girmeyi iptal ettik (sadece CAD birleştirme hatası vermemesi için mikroskobik 0.1mm tolerans bıraktık).
        # Matematiksel çözümü Root Cap kapama algoritmasını değiştirerek yapacağız.
        r_inner = R_hub - 0.1 
        if r_stations[0] > r_inner:
            r_stations = np.insert(r_stations, 0, r_inner)
            chord_dist = np.insert(chord_dist, 0, chord_dist[0])
            theta_dist = np.insert(theta_dist, 0, theta_dist[0])
            
        if r_stations[-1] < R_prop - 0.05:
            # Ucu mantar gibi bombeli yapmamak için elips yerine doğal eğimiyle (lineer) uzatıyoruz
            # Böylece kanat diğer katmanlardan ayrılmaz, pürüzsüzce devam eder.
            slope_c = (chord_dist[-1] - chord_dist[-2]) / (r_stations[-1] - r_stations[-2])
            slope_th = (theta_dist[-1] - theta_dist[-2]) / (r_stations[-1] - r_stations[-2])
            
            c_tip = chord_dist[-1] + slope_c * (R_prop - r_stations[-1])
            # Aşırı küçülüp kırılmasın diye minimum %40'ta tut
            c_tip = max(c_tip, chord_dist[-1] * 0.4) 
            
            th_tip = theta_dist[-1] + slope_th * (R_prop - r_stations[-1])
            
            r_stations = np.append(r_stations, R_prop)
            chord_dist = np.append(chord_dist, c_tip)
            theta_dist = np.append(theta_dist, th_tip)
            
        N_radial = len(r_stations)
        
        X_base_raw, Y_base_raw = naca4(naca_str, n=N_airfoil)
            
        # Profilin Ters Dönme Hatası Çözümü: Hücum kenarı (Kalın taraf) akışa baksın diye X ekseni ters çevrildi.
        X_base = pitch_axis - X_base_raw 
        Y_base = Y_base_raw
        
        N_pts = len(X_base)
        
        self.mesh_vertices = []
        self.mesh_faces = []
        max_z_blade = 0
        
        r_root_real = r_stations[1]
        r_tip = r_stations[-1]
        
        for blade in range(N_blades):
            base_blade_angle = blade * (2 * np.pi / N_blades)
            blade_v_offset = len(self.mesh_vertices)
            
            for i, r in enumerate(r_stations):
                c = chord_dist[i]
                th = theta_dist[i]
                
                skew_rad = 0
                if r > r_root_real:
                    r_ratio = (r - r_root_real) / (r_tip - r_root_real)
                    skew_deg = max_skew_deg * (r_ratio ** 2)
                    skew_rad = math.radians(skew_deg)
                
                x_loc = X_base * c
                y_loc = Y_base * c
                
                s_arc = x_loc * np.cos(th) - y_loc * np.sin(th)
                Z_pitched = x_loc * np.sin(th) + y_loc * np.cos(th)
                
                if np.max(np.abs(Z_pitched)) > max_z_blade:
                    max_z_blade = np.max(np.abs(Z_pitched))
                
                phi = np.zeros_like(s_arc)
                if r > 0.001:
                    phi = s_arc / r
                
                current_angle = base_blade_angle - skew_rad + phi
                
                X_final = r * np.cos(current_angle)
                Y_final = r * np.sin(current_angle)
                Z_final = Z_pitched
                
                for j in range(len(X_final)):
                    self.mesh_vertices.append([X_final[j], Y_final[j], Z_final[j]])
                    
            for i in range(N_radial - 1):
                for j in range(N_pts):
                    p1 = blade_v_offset + i*N_pts + j
                    p2 = blade_v_offset + i*N_pts + (j + 1) % N_pts
                    p3 = blade_v_offset + (i+1)*N_pts + j
                    p4 = blade_v_offset + (i+1)*N_pts + (j + 1) % N_pts
                    
                    self.mesh_faces.append([p1, p3, p2])
                    self.mesh_faces.append([p2, p3, p4])
                    
            # Kök Kapama (Root Cap) Matematiksel Çözümü: Cylindrical Center Fan
            # Kanat kökü silindirik bir hilal (crescent) şeklinde olduğu için zipping yöntemi secant (kiriş) taşmasına yol açar.
            # Bunun yerine, noktaları tam silindir yüzeyindeki matematiksel perdeleme merkezine (Pitch Axis) bağlıyoruz.
            r_root = r_stations[0]
            skew_rad_root = max_skew_deg * (math.pi/180) * (r_root / R_prop)**2
            
            # Tam silindir yüzeyindeki merkez nokta
            current_angle_center = base_blade_angle - skew_rad_root
            X_center = r_root * np.cos(current_angle_center)
            Y_center = r_root * np.sin(current_angle_center)
            Z_center = 0.0
            
            root_center_idx = len(self.mesh_vertices)
            self.mesh_vertices.append([X_center, Y_center, Z_center])
            
            for j in range(N_pts):
                p1 = blade_v_offset + j
                p2 = blade_v_offset + (j + 1) % N_pts
                self.mesh_faces.append([root_center_idx, p2, p1])
                
            # Tip Cap Zipping (No center point, prevents dimple)
            tip_offset = blade_v_offset + (N_radial - 1) * N_pts
            for j in range(N_airfoil - 1):
                p1 = tip_offset + j
                p2 = tip_offset + j + 1
                p3 = tip_offset + (N_pts - 1 - j)
                p4 = tip_offset + (N_pts - 2 - j)
                if p2 != p4:
                    self.mesh_faces.append([p1, p2, p3])
                    self.mesh_faces.append([p2, p4, p3])
                else:
                    self.mesh_faces.append([p1, p2, p3])
                
        if L_hub < 2 * max_z_blade + 2:
            L_hub = 2 * max_z_blade + 4
            self.vars["Hub Uzunluğu [mm]"].set(round(L_hub, 1))
                    
        N_th = 36
        theta_hub = np.linspace(0, 2*np.pi, N_th, endpoint=False)
        v_offset = len(self.mesh_vertices)
        
        for th in theta_hub:
            self.mesh_vertices.append([R_hub * np.cos(th), R_hub * np.sin(th), -L_hub/2])
        for th in theta_hub:
            self.mesh_vertices.append([R_hub * np.cos(th), R_hub * np.sin(th), L_hub/2]) 
            
        for i in range(N_th):
            p1 = v_offset + i
            p2 = v_offset + (i + 1) % N_th
            p3 = v_offset + N_th + i
            p4 = v_offset + N_th + (i + 1) % N_th
            self.mesh_faces.append([p1, p2, p3])
            self.mesh_faces.append([p2, p4, p3])
            
        center_bot_idx = len(self.mesh_vertices)
        self.mesh_vertices.append([0, 0, -L_hub/2])
        for i in range(N_th):
            self.mesh_faces.append([center_bot_idx, v_offset + (i+1)%N_th, v_offset + i])
            
        center_top_idx = len(self.mesh_vertices)
        self.mesh_vertices.append([0, 0, L_hub/2])
        for i in range(N_th):
            self.mesh_faces.append([center_top_idx, v_offset + N_th + i, v_offset + N_th + (i+1)%N_th])
            
        self.mesh_vertices = np.array(self.mesh_vertices)
        self.mesh_faces = np.array(self.mesh_faces)
        self.log.insert(tk.END, f"Geometri Tamamlandı: {len(self.mesh_vertices)} Nokta, {len(self.mesh_faces)} Yüzey.\n")
        
        self.update_performance_label()
        
        return True

    def generate_and_plot(self):
        if self.current_data is None: return
        self.log.insert(tk.END, "Çizim yenileniyor...\n")
        if not self.generate_geometry(): return
            
        self.ax.clear()
        
        x, y, z = self.mesh_vertices[:, 0], self.mesh_vertices[:, 1], self.mesh_vertices[:, 2]
        self.ax.plot_trisurf(x, y, self.mesh_faces, z, color='#c0c0c0', edgecolor='#404040', alpha=1.0, antialiased=True, linewidth=0.2)
        
        lim = self.vars["Pervane Dış Çapı [mm]"].get() / 2 * 1.1
        self.ax.set_xlim([-lim, lim])
        self.ax.set_ylim([-lim, lim])
        self.ax.set_zlim([-lim, lim])
        self.ax.set_box_aspect([1, 1, 1])
        
        self.ax.xaxis.pane.fill = False
        self.ax.yaxis.pane.fill = False
        self.ax.zaxis.pane.fill = False
        
        self.ax.xaxis.pane.set_edgecolor('#DDDDDD')
        self.ax.yaxis.pane.set_edgecolor('#DDDDDD')
        self.ax.zaxis.pane.set_edgecolor('#DDDDDD')
        
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])
        self.ax.set_zticklabels([])
        
        self.ax.grid(True)
        self.canvas.draw()

    def export_mesh(self, format_type):
        if self.current_data is None: return
        self.log.insert(tk.END, f"{format_type.upper()} hazırlanıyor...\n")
        
        # Geometriyi ekrandaki çözünürlükle oluştur
        if not self.generate_geometry(): return
        
        if len(self.mesh_faces) == 0:
            messagebox.showwarning("Uyarı", "Geometri boş!")
            return
            
        file_path = filedialog.asksaveasfilename(
            title=f"{format_type.upper()} Olarak Kaydet",
            defaultextension=f".{format_type}", 
            filetypes=[(f"{format_type.upper()} Dosyası", f"*.{format_type}")], 
            initialfile=f"PropellerGen_{format_type.upper()}"
        )
        
        if not file_path: 
            return
            
        try:
            self.log.insert(tk.END, f"{format_type.upper()} dosyası oluşturuluyor...\n")
            with open(file_path, 'w') as f:
                if format_type == 'stl':
                    f.write("solid pervane\n")
                    for face in self.mesh_faces:
                        v1, v2, v3 = self.mesh_vertices[face[0]], self.mesh_vertices[face[1]], self.mesh_vertices[face[2]]
                        u, w = v2 - v1, v3 - v1
                        n = np.cross(u, w)
                        n_norm = np.linalg.norm(n)
                        if n_norm > 0: n = n / n_norm
                        f.write(f"  facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
                        f.write("    outer loop\n")
                        f.write(f"      vertex {v1[0]:.6f} {v1[1]:.6f} {v1[2]:.6f}\n")
                        f.write(f"      vertex {v2[0]:.6f} {v2[1]:.6f} {v2[2]:.6f}\n")
                        f.write(f"      vertex {v3[0]:.6f} {v3[1]:.6f} {v3[2]:.6f}\n")
                        f.write("    endloop\n")
                        f.write("  endfacet\n")
                    f.write("endsolid pervane\n")
                elif format_type == 'obj':
                    f.write("# PropellerGen OBJ Export\n")
                    for v in self.mesh_vertices:
                        f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                    for face in self.mesh_faces:
                        f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
                        
            messagebox.showinfo("Başarılı", f"{format_type.upper()} Modeli kaydedildi:\n{file_path}")
            self.log.insert(tk.END, f"{format_type.upper()} dışa aktarıldı.\n")
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt hatası:\n{e}")
            
        # Dışa aktarım bittikten sonra görünümü bozmamak için varsayılan çözünürlüğe geri dön
        self.generate_geometry()

if __name__ == "__main__":
    root = tk.Tk()
    app = PropellerGenApp(root)
    root.mainloop()
