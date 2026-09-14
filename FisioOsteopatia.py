import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, hashlib, secrets, shutil
from pathlib import Path
from datetime import datetime
import csv

APP = "Fisio-Osteopatia"
ROOT = Path.home() / "FisioOsteopatia"
ROOT.mkdir(exist_ok=True)
DB = ROOT / "fisio_osteopatia.db"
BACKUPS = ROOT / "Copias"
BACKUPS.mkdir(exist_ok=True)

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def hashpw(pw, salt=None):
    salt = salt or secrets.token_bytes(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 180000)
    return salt.hex()+":"+h.hex()

def checkpw(pw, stored):
    try:
        s,h = stored.split(":")
        x = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(s), 180000).hex()
        return secrets.compare_digest(x,h)
    except Exception:
        return False

def init_db():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'admin');
    CREATE TABLE IF NOT EXISTS patients(
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT, email TEXT, birth TEXT,
      address TEXT, allergies TEXT, medication TEXT, history TEXT, notes TEXT,
      created TEXT, updated TEXT);
    CREATE TABLE IF NOT EXISTS sessions(
      id INTEGER PRIMARY KEY, patient_id INTEGER, date TEXT, pain INTEGER,
      assessment TEXT, treatment TEXT, exercises TEXT, evolution TEXT,
      FOREIGN KEY(patient_id) REFERENCES patients(id));
    CREATE TABLE IF NOT EXISTS appointments(
      id INTEGER PRIMARY KEY, patient_id INTEGER, date TEXT, time TEXT,
      reason TEXT, notes TEXT, FOREIGN KEY(patient_id) REFERENCES patients(id));
    CREATE TABLE IF NOT EXISTS audit(
      id INTEGER PRIMARY KEY, username TEXT, action TEXT, moment TEXT);
    """)
    if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)",
                  ("admin",hashpw("admin"),"admin"))
    c.commit(); c.close()

def audit(user, action):
    c=conn(); c.execute("INSERT INTO audit(username,action,moment) VALUES(?,?,?)",
                        (user,action,datetime.now().strftime("%Y-%m-%d %H:%M:%S"))); c.commit(); c.close()

class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fisio-Osteopatía — Acceso")
        self.geometry("430x300"); self.resizable(False,False)
        ttk.Label(self,text="FISIO-OSTEOPATÍA",font=("Segoe UI",20,"bold")).pack(pady=(35,8))
        ttk.Label(self,text="Historia clínica y gestión de consulta").pack(pady=(0,25))
        f=ttk.Frame(self); f.pack()
        ttk.Label(f,text="Usuario").grid(row=0,column=0,padx=8,pady=8,sticky="e")
        self.u=ttk.Entry(f,width=28); self.u.grid(row=0,column=1)
        ttk.Label(f,text="Contraseña").grid(row=1,column=0,padx=8,pady=8,sticky="e")
        self.p=ttk.Entry(f,width=28,show="*"); self.p.grid(row=1,column=1)
        ttk.Button(self,text="Entrar",command=self.login).pack(pady=20)
        ttk.Label(self,text="Primer acceso: admin / admin",foreground="#555").pack()
        self.bind("<Return>",lambda e:self.login())
    def login(self):
        c=conn(); r=c.execute("SELECT * FROM users WHERE username=?",(self.u.get().strip(),)).fetchone(); c.close()
        if r and checkpw(self.p.get(),r["password"]):
            audit(r["username"],"Inicio de sesión")
            self.destroy(); Main(r["username"],r["role"]).mainloop()
        else: messagebox.showerror("Acceso","Usuario o contraseña incorrectos.")

class Main(tk.Tk):
    def __init__(self,user,role):
        super().__init__(); self.user=user; self.role=role; self.selected=None
        self.title("Fisio-Osteopatía"); self.geometry("1180x760"); self.minsize(1000,650)
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.build()
        self.refresh_patients()
        self.refresh_agenda()
    def build(self):
        top=ttk.Frame(self,padding=10); top.pack(fill="x")
        ttk.Label(top,text="FISIO-OSTEOPATÍA",font=("Segoe UI",18,"bold")).pack(side="left")
        ttk.Label(top,text=f"  Usuario: {self.user}",foreground="#555").pack(side="left",padx=15)
        ttk.Button(top,text="Copia de seguridad",command=self.backup).pack(side="right",padx=5)
        ttk.Button(top,text="Exportar pacientes",command=self.export_csv).pack(side="right",padx=5)
        nb=ttk.Notebook(self); nb.pack(fill="both",expand=True,padx=10,pady=(0,10))
        self.tab_pat=ttk.Frame(nb); self.tab_clin=ttk.Frame(nb); self.tab_ag=ttk.Frame(nb)
        self.tab_info=ttk.Frame(nb)
        nb.add(self.tab_pat,text="Pacientes"); nb.add(self.tab_clin,text="Historia clínica")
        nb.add(self.tab_ag,text="Agenda"); nb.add(self.tab_info,text="Ayuda")
        self.build_patients(); self.build_clinical(); self.build_agenda(); self.build_info()
    def build_patients(self):
        left=ttk.Frame(self.tab_pat,padding=10); left.pack(side="left",fill="y")
        ttk.Label(left,text="Buscar").pack(anchor="w")
        self.search=ttk.Entry(left,width=30); self.search.pack(fill="x",pady=5)
        self.search.bind("<KeyRelease>",lambda e:self.refresh_patients())
        self.lst=ttk.Treeview(left,columns=("id","name","phone"),show="headings",height=28)
        for col,txt,w in [("id","ID",50),("name","Paciente",210),("phone","Teléfono",110)]:
            self.lst.heading(col,text=txt); self.lst.column(col,width=w)
        self.lst.pack(fill="both",expand=True,pady=5); self.lst.bind("<<TreeviewSelect>>",self.select_patient)
        bf=ttk.Frame(left); bf.pack(fill="x")
        ttk.Button(bf,text="Nuevo",command=self.new_patient).pack(side="left",padx=2)
        ttk.Button(bf,text="Editar",command=self.edit_patient).pack(side="left",padx=2)
        ttk.Button(bf,text="Eliminar",command=self.delete_patient).pack(side="left",padx=2)
        right=ttk.Frame(self.tab_pat,padding=10); right.pack(side="left",fill="both",expand=True)
        self.pvars={}
        fields=[("name","Nombre completo"),("phone","Teléfono"),("email","Email"),("birth","Fecha nacimiento"),
                ("address","Dirección")]
        for i,(k,t) in enumerate(fields):
            ttk.Label(right,text=t).grid(row=i,column=0,sticky="w",pady=5)
            v=tk.StringVar(); self.pvars[k]=v; ttk.Entry(right,textvariable=v,width=55).grid(row=i,column=1,sticky="ew",pady=5)
        ttk.Label(right,text="Alergias").grid(row=5,column=0,sticky="nw",pady=5); self.allerg=tk.Text(right,height=3,width=55); self.allerg.grid(row=5,column=1,sticky="ew")
        ttk.Label(right,text="Medicación").grid(row=6,column=0,sticky="nw",pady=5); self.meds=tk.Text(right,height=3,width=55); self.meds.grid(row=6,column=1,sticky="ew")
        ttk.Label(right,text="Antecedentes").grid(row=7,column=0,sticky="nw",pady=5); self.hist=tk.Text(right,height=5,width=55); self.hist.grid(row=7,column=1,sticky="ew")
        ttk.Label(right,text="Notas").grid(row=8,column=0,sticky="nw",pady=5); self.notes=tk.Text(right,height=5,width=55); self.notes.grid(row=8,column=1,sticky="ew")
        ttk.Button(right,text="Guardar ficha",command=self.save_patient).grid(row=9,column=1,sticky="e",pady=12)
        right.columnconfigure(1,weight=1)
    def build_clinical(self):
        f=ttk.Frame(self.tab_clin,padding=15); f.pack(fill="both",expand=True)
        self.cl_title=ttk.Label(f,text="Seleccione un paciente",font=("Segoe UI",14,"bold")); self.cl_title.pack(anchor="w")
        row=ttk.Frame(f); row.pack(fill="x",pady=12)
        ttk.Label(row,text="Dolor EVA (0-10)").pack(side="left")
        self.eva=tk.IntVar(value=0); ttk.Spinbox(row,from_=0,to=10,textvariable=self.eva,width=5).pack(side="left",padx=8)
        ttk.Label(row,text="Fecha").pack(side="left",padx=(25,5)); self.sdate=tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(row,textvariable=self.sdate,width=12).pack(side="left")
        self.ctext={}
        labels=["Valoración fisioterapéutica / osteopática","Exploración, palpación, movilidad y tests","Tratamiento y técnicas aplicadas","Ejercicios y pautas domiciliarias","Evolución / observaciones"]
        for lab in labels:
            ttk.Label(f,text=lab).pack(anchor="w",pady=(8,2))
            t=tk.Text(f,height=5); t.pack(fill="x"); self.ctext[lab]=t
        ttk.Button(f,text="Guardar sesión",command=self.save_session).pack(anchor="e",pady=12)
    def build_agenda(self):
        f=ttk.Frame(self.tab_ag,padding=15); f.pack(fill="both",expand=True)
        form=ttk.LabelFrame(f,text="Nueva cita",padding=10); form.pack(fill="x")
        self.avars={}
        for i,(k,lab,w) in enumerate([("date","Fecha (AAAA-MM-DD)",14),("time","Hora",8),("reason","Motivo",35)]):
            ttk.Label(form,text=lab).grid(row=0,column=i*2,padx=5)
            v=tk.StringVar(value=datetime.now().strftime("%Y-%m-%d") if k=="date" else "")
            self.avars[k]=v; ttk.Entry(form,textvariable=v,width=w).grid(row=0,column=i*2+1,padx=5)
        ttk.Button(form,text="Añadir cita",command=self.add_appointment).grid(row=0,column=7,padx=10)
        self.ag=ttk.Treeview(f,columns=("id","date","time","patient","reason"),show="headings",height=25)
        for c,t,w in [("id","ID",50),("date","Fecha",110),("time","Hora",80),("patient","Paciente",230),("reason","Motivo",300)]:
            self.ag.heading(c,text=t); self.ag.column(c,width=w)
        self.ag.pack(fill="both",expand=True,pady=12)
        ttk.Button(f,text="Eliminar cita seleccionada",command=self.del_appointment).pack(anchor="e")
    def build_info(self):
        f=ttk.Frame(self.tab_info,padding=30); f.pack(fill="both",expand=True)
        ttk.Label(f,text="Fisio-Osteopatía",font=("Segoe UI",20,"bold")).pack(anchor="w",pady=10)
        text=("Aplicación local para gestión de pacientes de fisioterapia y osteopatía.\n\n"
              "Los datos se guardan en el ordenador, en la carpeta FisioOsteopatia de tu usuario de Windows.\n"
              "Haz copias de seguridad periódicas.\n\n"
              "Primer acceso: admin / admin\n\n"
              "Esta versión es una herramienta de gestión y debe adaptarse a los requisitos legales, "
              "de privacidad y protección de datos aplicables a tu consulta antes de usarla con historias clínicas reales.")
        ttk.Label(f,text=text,justify="left",wraplength=850).pack(anchor="w")
    def refresh_patients(self):
        q=self.search.get().strip() if hasattr(self,"search") else ""
        for x in self.lst.get_children(): self.lst.delete(x)
        c=conn(); rows=c.execute("SELECT id,name,phone FROM patients WHERE name LIKE ? ORDER BY name",("%"+q+"%",)).fetchall(); c.close()
        for r in rows:self.lst.insert("", "end", values=(r["id"],r["name"],r["phone"] or ""))
    def select_patient(self,e=None):
        s=self.lst.selection()
        if not s:return
        self.selected=int(self.lst.item(s[0],"values")[0]); self.load_patient()
    def load_patient(self):
        c=conn(); r=c.execute("SELECT * FROM patients WHERE id=?",(self.selected,)).fetchone(); c.close()
        if not r:return
        for k in self.pvars:self.pvars[k].set(r[k] or "")
        for w,val in [(self.allerg,r["allergies"]),(self.meds,r["medication"]),(self.hist,r["history"]),(self.notes,r["notes"])]:
            w.delete("1.0","end"); w.insert("1.0",val or "")
        self.cl_title.config(text=f"Historia clínica — {r['name']}")
        self.load_sessions()
    def new_patient(self):
        self.selected=None
        for v in self.pvars.values():v.set("")
        for w in [self.allerg,self.meds,self.hist,self.notes]:w.delete("1.0","end")
        self.cl_title.config(text="Nuevo paciente")
    def edit_patient(self): self.load_patient() if self.selected else self.new_patient()
    def save_patient(self):
        name=self.pvars["name"].get().strip()
        if not name: return messagebox.showwarning("Paciente","El nombre es obligatorio.")
        now=datetime.now().isoformat(timespec="seconds")
        vals=[self.pvars[k].get().strip() for k in self.pvars]
        vals += [self.allerg.get("1.0","end").strip(),self.meds.get("1.0","end").strip(),
                 self.hist.get("1.0","end").strip(),self.notes.get("1.0","end").strip()]
        c=conn()
        if self.selected:
            c.execute("""UPDATE patients SET name=?,phone=?,email=?,birth=?,address=?,allergies=?,medication=?,history=?,notes=?,updated=? WHERE id=?""",(*vals,now,self.selected))
        else:
            c.execute("""INSERT INTO patients(name,phone,email,birth,address,allergies,medication,history,notes,created,updated)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(*vals,now,now)); self.selected=c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.commit(); c.close(); audit(self.user,"Guardó paciente"); self.refresh_patients(); self.load_patient()
        messagebox.showinfo("Guardado","Ficha guardada correctamente.")
    def delete_patient(self):
        if not self.selected:return
        if not messagebox.askyesno("Eliminar","¿Eliminar el paciente y sus citas/sesiones?"):return
        c=conn(); c.execute("DELETE FROM sessions WHERE patient_id=?",(self.selected,)); c.execute("DELETE FROM appointments WHERE patient_id=?",(self.selected,)); c.execute("DELETE FROM patients WHERE id=?",(self.selected,)); c.commit(); c.close()
        audit(self.user,"Eliminó paciente"); self.selected=None; self.refresh_patients(); self.new_patient()
    def save_session(self):
        if not self.selected:return messagebox.showwarning("Paciente","Selecciona un paciente.")
        labs=list(self.ctext); vals=[self.ctext[x].get("1.0","end").strip() for x in labs]
        c=conn(); c.execute("""INSERT INTO sessions(patient_id,date,pain,assessment,treatment,exercises,evolution)
             VALUES(?,?,?,?,?,?,?)""",(self.selected,self.sdate.get(),self.eva.get(),*vals)); c.commit(); c.close()
        audit(self.user,"Guardó sesión clínica"); messagebox.showinfo("Sesión","Sesión guardada.")
    def load_sessions(self):
        pass
    def add_appointment(self):
        if not self.selected:return messagebox.showwarning("Paciente","Selecciona un paciente en la pestaña Pacientes.")
        c=conn(); c.execute("INSERT INTO appointments(patient_id,date,time,reason) VALUES(?,?,?,?)",
                            (self.selected,self.avars["date"].get(),self.avars["time"].get(),self.avars["reason"].get())); c.commit(); c.close()
        audit(self.user,"Añadió cita"); self.refresh_agenda()
    def refresh_agenda(self):
        if not hasattr(self,"ag"):return
        for x in self.ag.get_children():self.ag.delete(x)
        c=conn(); rows=c.execute("""SELECT a.*,p.name FROM appointments a JOIN patients p ON p.id=a.patient_id
                                    ORDER BY a.date,a.time""").fetchall(); c.close()
        for r in rows:self.ag.insert("", "end", values=(r["id"],r["date"],r["time"],r["name"],r["reason"] or ""))
    def del_appointment(self):
        s=self.ag.selection()
        if not s:return
        aid=self.ag.item(s[0],"values")[0]
        c=conn(); c.execute("DELETE FROM appointments WHERE id=?",(aid,)); c.commit(); c.close(); self.refresh_agenda()
    def backup(self):
        c=conn(); c.execute("PRAGMA wal_checkpoint(FULL)"); c.close()
        dest=BACKUPS/f"copia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"; shutil.copy2(DB,dest)
        audit(self.user,"Creó copia de seguridad"); messagebox.showinfo("Copia","Copia creada en:\n"+str(dest))
    def export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV","*.csv")],initialfile="pacientes.csv")
        if not path:return
        c=conn(); rows=c.execute("SELECT id,name,phone,email,birth,address,allergies,medication,history,notes FROM patients ORDER BY name").fetchall(); c.close()
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w=csv.writer(f); w.writerow(rows[0].keys() if rows else ["id","name","phone","email","birth","address","allergies","medication","history","notes"])
            for r in rows:w.writerow(list(r))
        messagebox.showinfo("Exportación","Archivo CSV creado.")
    def close(self):
        audit(self.user,"Cierre de aplicación"); self.destroy()

init_db()
Login().mainloop()
