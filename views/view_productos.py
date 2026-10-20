import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Producto, Categoria, Proveedor
import time

class VistaProductos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.categorias_dict = {}
        self.proveedores_list = []
        self.sku_edicion = None
        self.colores_lista = ["Negro", "Blanco", "Azul", "Amarillo", "Rojo", "Verde","Verde Limon","Morado","Fucsia","Naranja","Rosada", "Gris", "Otro"]

        ctk.CTkLabel(self, text="Gestión de Productos", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        frame_form = ctk.CTkFrame(self, corner_radius=10)
        frame_form.pack(fill="x", pady=(0, 10), ipady=10)

        # Fila 1
        ctk.CTkLabel(frame_form, text="Categoría:").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.combo_cat = ctk.CTkOptionMenu(frame_form, values=["Cargando..."], command=self.autocompletar_nombre)
        self.combo_cat.grid(row=0, column=1, padx=15, pady=10)

        ctk.CTkLabel(frame_form, text="Nombre del Producto:").grid(row=0, column=2, padx=15, pady=10, sticky="w")
        self.entry_nombre = ctk.CTkEntry(frame_form, width=200)
        self.entry_nombre.grid(row=0, column=3, padx=15, pady=10)

        # Fila 2
        ctk.CTkLabel(frame_form, text="Proveedor:").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.combo_prov = ctk.CTkOptionMenu(frame_form, values=["Cargando..."])
        self.combo_prov.grid(row=1, column=1, padx=15, pady=10)

        ctk.CTkLabel(frame_form, text="Dimensión/Talla:").grid(row=1, column=2, padx=15, pady=10, sticky="w")
        self.entry_dim = ctk.CTkEntry(frame_form, width=150, placeholder_text="Ej: 11 oz, Talla M, 20x30")
        self.entry_dim.grid(row=1, column=3, padx=15, pady=10, sticky="w")

        ctk.CTkLabel(frame_form, text="Color:").grid(row=1, column=4, padx=5, pady=10, sticky="w")
        self.combo_color = ctk.CTkOptionMenu(frame_form, width=120, values=self.colores_lista)
        self.combo_color.grid(row=1, column=5, padx=15, pady=10, sticky="w")

        # Fila 3
        ctk.CTkLabel(frame_form, text="Precio Venta ($):").grid(row=2, column=0, padx=15, pady=10, sticky="w")
        self.entry_precio = ctk.CTkEntry(frame_form, width=100)
        self.entry_precio.grid(row=2, column=1, padx=15, pady=10, sticky="w")

        ctk.CTkLabel(frame_form, text="Stock Inicial:").grid(row=2, column=2, padx=15, pady=10, sticky="w")
        self.entry_stock = ctk.CTkEntry(frame_form, width=70)
        self.entry_stock.grid(row=2, column=3, padx=15, pady=10, sticky="w")

        self.btn_guardar = ctk.CTkButton(frame_form, text="Guardar Producto", fg_color="#28a745", hover_color="#218838", command=self.guardar_producto)
        self.btn_guardar.grid(row=2, column=4, columnspan=2, pady=15)

        # --- BOTONES DE ACCIÓN Y BUSCADOR ---
        frame_acciones = ctk.CTkFrame(self, fg_color="transparent")
        frame_acciones.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(frame_acciones, text="✏️ Editar Seleccionado", command=self.preparar_edicion).pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_acciones, text="🗑️ Eliminar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.eliminar_producto).pack(side="left")
        
        # Nuevo buscador alineado a la derecha
        self.entry_filtro = ctk.CTkEntry(frame_acciones, width=250, placeholder_text="🔍 Buscar producto, color, talla...")
        self.entry_filtro.pack(side="right")
        self.entry_filtro.bind("<KeyRelease>", lambda e: self.cargar_productos(self.entry_filtro.get()))

        # Tabla
        self.aplicar_estilo_tabla()
        self.tree = ttk.Treeview(self, columns=("cod", "cat", "nombre", "prov", "dim", "color", "precio", "stock"), show="headings", height=15)
        self.tree.heading("cod", text="Código")
        self.tree.heading("cat", text="Categoría")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("prov", text="Proveedor")
        self.tree.heading("dim", text="Medida/Talla")
        self.tree.heading("color", text="Color")
        self.tree.heading("precio", text="Precio Venta")
        self.tree.heading("stock", text="Stock")
        
        self.tree.column("cod", width=120, stretch=False)
        self.tree.column("cat", width=130)
        self.tree.column("nombre", width=180)
        self.tree.column("prov", width=120)
        self.tree.column("dim", width=100)
        self.tree.column("color", width=80)
        self.tree.column("precio", width=100, anchor="e")
        self.tree.column("stock", width=60, anchor="center", stretch=False)
        self.tree.pack(fill="both", expand=True)

        self.cargar_datos_desplegables()
        self.cargar_productos()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def autocompletar_nombre(self, seleccion):
        if not self.sku_edicion:
            self.entry_nombre.delete(0, 'end')
            self.entry_nombre.insert(0, seleccion)

    def cargar_datos_desplegables(self):
        with SessionLocal() as db:
            categorias = db.query(Categoria).all()
            if categorias:
                self.categorias_dict = {c.nombre: c.id for c in categorias}
                self.combo_cat.configure(values=list(self.categorias_dict.keys()))
                self.combo_cat.set(list(self.categorias_dict.keys())[0])
            else:
                self.combo_cat.configure(values=["Sin categorías"])
                self.combo_cat.set("Sin categorías")

            proveedores = db.query(Proveedor).all()
            if proveedores:
                self.proveedores_list = [p.nombre for p in proveedores]
                self.combo_prov.configure(values=self.proveedores_list)
                self.combo_prov.set(self.proveedores_list[0])
            else:
                self.combo_prov.configure(values=["Sin proveedores"])
                self.combo_prov.set("Sin proveedores")

    def preparar_edicion(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        
        item = self.tree.item(seleccion[0])
        self.sku_edicion = item['values'][0]
        
        self.combo_cat.set(item['values'][1])
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, item['values'][2])
        self.combo_prov.set(item['values'][3])
        self.entry_dim.delete(0, 'end')
        self.entry_dim.insert(0, item['values'][4])
        self.combo_color.set(item['values'][5])
        
        precio_limpio = str(item['values'][6]).replace("$ ", "").replace(",", "")
        self.entry_precio.delete(0, 'end')
        self.entry_precio.insert(0, precio_limpio)
        self.entry_stock.delete(0, 'end')
        self.entry_stock.insert(0, item['values'][7])
        
        self.btn_guardar.configure(text="Actualizar Producto", fg_color="#ffc107", text_color="black")

    def guardar_producto(self):
        nombre = self.entry_nombre.get()
        cat_nombre = self.combo_cat.get()
        prov_nombre = self.combo_prov.get()
        dim = self.entry_dim.get()
        color = self.combo_color.get()
        precio = float(self.entry_precio.get() or 0)
        stock = int(self.entry_stock.get() or 0)

        if nombre and cat_nombre in self.categorias_dict:
            cat_id = self.categorias_dict[cat_nombre]
            
            with SessionLocal() as db:
                if self.sku_edicion:
                    prod = db.query(Producto).filter(Producto.sku == self.sku_edicion).first()
                    if prod:
                        prod.nombre = nombre
                        prod.dimensiones = dim
                        prod.color = color
                        prod.precio_venta = precio
                        prod.stock_actual = stock
                        prod.categoria_id = cat_id
                        prod.proveedor_habitual = prov_nombre
                    self.sku_edicion = None
                    self.btn_guardar.configure(text="Guardar Producto", fg_color="#28a745", text_color="white")
                else:
                    codigo_interno = f"PRD-{int(time.time())}" 
                    nuevo_prod = Producto(
                        sku=codigo_interno, nombre=nombre, dimensiones=dim, color=color, 
                        precio_venta=precio, stock_actual=stock, categoria_id=cat_id, proveedor_habitual=prov_nombre
                    )
                    db.add(nuevo_prod)
                
                db.commit()
            
            for entry in (self.entry_nombre, self.entry_dim, self.entry_precio, self.entry_stock):
                entry.delete(0, 'end')
            self.combo_color.set(self.colores_lista[0])
                
            self.cargar_productos()

    def eliminar_producto(self):
        seleccion = self.tree.selection()
        if not seleccion: return
        
        sku = self.tree.item(seleccion[0])['values'][0]
        with SessionLocal() as db:
            prod = db.query(Producto).filter(Producto.sku == sku).first()
            if prod:
                db.delete(prod)
                db.commit()
        self.cargar_productos()

    def cargar_productos(self, filtro_texto=""):
        for item in self.tree.get_children(): self.tree.delete(item)
        filtro_texto = filtro_texto.lower()
        
        with SessionLocal() as db:
            for p in db.query(Producto).all():
                cat_nombre = p.categoria.nombre if p.categoria else "N/A"
                dim_str = p.dimensiones if p.dimensiones else "N/A"
                color_str = p.color if p.color else "N/A"
                
                texto_fila = f"{p.sku} {cat_nombre} {p.nombre} {p.proveedor_habitual} {dim_str} {color_str}".lower()
                
                if filtro_texto in texto_fila:
                    self.tree.insert("", "end", values=(
                        p.sku, cat_nombre, p.nombre, p.proveedor_habitual, 
                        dim_str, color_str, f"$ {p.precio_venta:,.0f}", p.stock_actual
                    ))