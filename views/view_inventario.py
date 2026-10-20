import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Producto

class VistaInventario(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self, text="Control de Inventario", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10), anchor="w")

        # --- BUSCADOR ---
        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(frame_top, text="🔍 Buscar:").pack(side="left", padx=(0, 10))
        self.entry_filtro = ctk.CTkEntry(frame_top, width=350, placeholder_text="Buscar por código, nombre, color o estado...")
        self.entry_filtro.pack(side="left")
        self.entry_filtro.bind("<KeyRelease>", lambda e: self.cargar_inventario(self.entry_filtro.get()))

        # --- TABLA DE INVENTARIO ---
        self.aplicar_estilo_tabla()
        # NUEVA COLUMNA DE COLOR AGREGADA AQUÍ
        self.tree = ttk.Treeview(self, columns=("cod", "nombre", "color", "precio", "stock", "estado"), show="headings", height=20)
        self.tree.heading("cod", text="Código")
        self.tree.heading("nombre", text="Producto")
        self.tree.heading("color", text="Color") 
        self.tree.heading("precio", text="Precio Venta")
        self.tree.heading("stock", text="Stock Actual")
        self.tree.heading("estado", text="Estado")
        
        self.tree.column("cod", width=120)
        self.tree.column("nombre", width=220)
        self.tree.column("color", width=100, anchor="center")
        self.tree.column("precio", width=100, anchor="e")
        self.tree.column("stock", width=100, anchor="center")
        self.tree.column("estado", width=120, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="🔄 Actualizar Inventario", command=self.cargar_inventario).pack(pady=10)

        self.cargar_inventario()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def cargar_inventario(self, filtro_texto=""):
        for item in self.tree.get_children(): self.tree.delete(item)
        filtro_texto = filtro_texto.lower() 
        
        with SessionLocal() as db:
            productos = db.query(Producto).all()
            for p in productos:
                if p.stock_actual <= 0:
                    estado = "❌ AGOTADO"
                elif p.stock_actual <= p.stock_minimo:
                    estado = "⚠️ STOCK BAJO"
                else:
                    estado = "✅ DISPONIBLE"
                
                # Rescatamos el color del producto
                color_str = p.color if p.color else "N/A"
                texto_fila = f"{p.sku} {p.nombre} {color_str} {estado}".lower()
                
                if filtro_texto in texto_fila:
                    self.tree.insert("", "end", values=(p.sku, p.nombre, color_str, f"$ {p.precio_venta:,.0f}", p.stock_actual, estado))