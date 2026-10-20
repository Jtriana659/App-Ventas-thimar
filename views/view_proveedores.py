import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Proveedor

class VistaProveedores(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.id_edicion = None

        ctk.CTkLabel(self, text="Gestión de Proveedores", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        frame_form = ctk.CTkFrame(self, corner_radius=10)
        frame_form.pack(fill="x", pady=(0, 10), ipady=10)

        ctk.CTkLabel(frame_form, text="Nombre Proveedor:").grid(row=0, column=0, padx=15, pady=10)
        self.entry_nombre = ctk.CTkEntry(frame_form, width=200)
        self.entry_nombre.grid(row=0, column=1, padx=15, pady=10)
        
        ctk.CTkLabel(frame_form, text="Teléfono/WhatsApp:").grid(row=0, column=2, padx=15, pady=10)
        self.entry_tel = ctk.CTkEntry(frame_form, width=200)
        self.entry_tel.grid(row=0, column=3, padx=15, pady=10)

        self.btn_guardar = ctk.CTkButton(frame_form, text="Guardar Proveedor", fg_color="#28a745", hover_color="#218838", command=self.guardar_proveedor)
        self.btn_guardar.grid(row=1, column=0, columnspan=4, pady=15)

        frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        frame_acciones.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(frame_acciones, text="✏️ Editar Seleccionado", command=self.preparar_edicion).pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.eliminar_proveedor).pack(side="left")

        self.aplicar_estilo_tabla()
        self.tree = ttk.Treeview(self, columns=("id", "nombre", "tel"), show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Proveedor")
        self.tree.heading("tel", text="Teléfono")
        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True)
        self.cargar_proveedores()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def preparar_edicion(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        
        item = self.tree.item(seleccion[0])
        self.id_edicion = item['values'][0]
        
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, item['values'][1])
        
        self.entry_tel.delete(0, 'end')
        self.entry_tel.insert(0, item['values'][2])
        
        self.btn_guardar.configure(text="Actualizar Proveedor", fg_color="#ffc107", text_color="black")

    def guardar_proveedor(self):
        nombre = self.entry_nombre.get()
        if nombre:
            with SessionLocal() as db:
                if self.id_edicion:
                    prov = db.query(Proveedor).filter(Proveedor.id == self.id_edicion).first()
                    if prov:
                        prov.nombre = nombre
                        prov.telefono = self.entry_tel.get()
                    self.id_edicion = None
                    self.btn_guardar.configure(text="Guardar Proveedor", fg_color="#28a745", text_color="white")
                else:
                    db.add(Proveedor(nombre=nombre, telefono=self.entry_tel.get()))
                db.commit()
            
            self.entry_nombre.delete(0, 'end')
            self.entry_tel.delete(0, 'end')
            self.cargar_proveedores()

    def eliminar_proveedor(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        
        id_prov = self.tree.item(seleccion[0])['values'][0]
        with SessionLocal() as db:
            prov = db.query(Proveedor).filter(Proveedor.id == id_prov).first()
            if prov:
                db.delete(prov)
                db.commit()
        self.cargar_proveedores()

    def cargar_proveedores(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        with SessionLocal() as db:
            for p in db.query(Proveedor).all():
                self.tree.insert("", "end", values=(p.id, p.nombre, p.telefono))