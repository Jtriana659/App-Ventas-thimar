import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Categoria

class VistaCategorias(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        self.id_edicion = None # Variable para saber si estamos editando

        ctk.CTkLabel(self, text="Gestión de Categorías", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # --- FORMULARIO ---
        frame_form = ctk.CTkFrame(self, corner_radius=10)
        frame_form.pack(fill="x", pady=(0, 10), ipady=10)

        ctk.CTkLabel(frame_form, text="Nombre de Categoría:").grid(row=0, column=0, padx=15, pady=15)
        self.entry_nombre = ctk.CTkEntry(frame_form, width=250, placeholder_text="Ej: Camisas Dama")
        self.entry_nombre.grid(row=0, column=1, padx=15, pady=15)

        self.btn_guardar = ctk.CTkButton(frame_form, text="Guardar Categoría", fg_color="#28a745", hover_color="#218838", command=self.guardar_categoria)
        self.btn_guardar.grid(row=0, column=2, padx=15)

        # --- BOTONES DE ACCIÓN (Lápiz y Balde) ---
        frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        frame_acciones.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(frame_acciones, text="✏️ Editar Seleccionado", command=self.preparar_edicion).pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.eliminar_categoria).pack(side="left")

        # --- TABLA ---
        self.aplicar_estilo_tabla()
        self.tree = ttk.Treeview(self, columns=("id", "nombre"), show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Categoría")
        self.tree.column("id", width=50)
        self.tree.pack(fill="both", expand=True)
        self.cargar_categorias()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def preparar_edicion(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        # Obtener los datos de la fila seleccionada
        item = self.tree.item(seleccion[0])
        id_cat = item['values'][0]
        nombre = item['values'][1]

        # Llenar el formulario
        self.id_edicion = id_cat
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, nombre)
        self.btn_guardar.configure(text="Actualizar Categoría", fg_color="#ffc107", text_color="black") # Cambia a amarillo

    def guardar_categoria(self):
        nombre = self.entry_nombre.get()
        if nombre:
            with SessionLocal() as db:
                if self.id_edicion: # MODO EDICIÓN
                    categoria = db.query(Categoria).filter(Categoria.id == self.id_edicion).first()
                    if categoria:
                        categoria.nombre = nombre
                    self.id_edicion = None
                    self.btn_guardar.configure(text="Guardar Categoría", fg_color="#28a745", text_color="white")
                else: # MODO CREACIÓN
                    db.add(Categoria(nombre=nombre))
                db.commit()
            
            self.entry_nombre.delete(0, 'end')
            self.cargar_categorias()

    def eliminar_categoria(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        
        id_cat = self.tree.item(seleccion[0])['values'][0]
        with SessionLocal() as db:
            categoria = db.query(Categoria).filter(Categoria.id == id_cat).first()
            if categoria:
                db.delete(categoria)
                db.commit()
        self.cargar_categorias()

    def cargar_categorias(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        with SessionLocal() as db:
            for c in db.query(Categoria).all():
                self.tree.insert("", "end", values=(c.id, c.nombre))