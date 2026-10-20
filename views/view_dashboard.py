import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Producto, Venta, DetalleVenta, TransaccionFinanciera
from sqlalchemy import func
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class VistaDashboard(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self, text="Dashboard - Resumen del Negocio", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # --- 1. PANEL DE TARJETAS (KPIs) ---
        self.frame_kpis = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_kpis.pack(fill="x", pady=(0, 20))
        
        self.lbl_caja = self.crear_tarjeta(self.frame_kpis, "Dinero en Caja (Real)", "$ 0", 0, "#28a745")
        self.lbl_inventario = self.crear_tarjeta(self.frame_kpis, "Valor del Inventario (Costo)", "$ 0", 1, "#17a2b8")
        self.lbl_ventas = self.crear_tarjeta(self.frame_kpis, "Total Ventas Acumuladas", "$ 0", 2, "#ffc107")

        # --- 2. CONTENEDOR INFERIOR (Gráfico y Alertas) ---
        self.frame_inferior = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_inferior.pack(fill="both", expand=True)
        
        # Columna Izquierda: Gráfico
        self.frame_grafico = ctk.CTkFrame(self.frame_inferior, corner_radius=10)
        self.frame_grafico.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(self.frame_grafico, text="Top 5 - Productos Más Vendidos", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # Columna Derecha: Alertas de Stock
        self.frame_alertas = ctk.CTkFrame(self.frame_inferior, corner_radius=10, width=350)
        self.frame_alertas.pack(side="right", fill="y")
        ctk.CTkLabel(self.frame_alertas, text="⚠️ Alertas de Stock Bajo", font=ctk.CTkFont(size=16, weight="bold"), text_color="#dc3545").pack(pady=10)
        
        # Tabla de Alertas
        self.aplicar_estilo_tabla()
        self.tree_alertas = ttk.Treeview(self.frame_alertas, columns=("nombre", "stock"), show="headings", height=10)
        self.tree_alertas.heading("nombre", text="Producto / Insumo")
        self.tree_alertas.heading("stock", text="Quedan")
        self.tree_alertas.column("stock", width=60, anchor="center")
        self.tree_alertas.pack(fill="both", expand=True, padx=10, pady=10)

        # Botón para refrescar
        ctk.CTkButton(self, text="🔄 Actualizar Dashboard", command=self.cargar_datos).pack(pady=15)

        self.cargar_datos()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#dc3545", foreground="white", font=('Arial', 10, 'bold'))

    def crear_tarjeta(self, master, titulo, valor, col, color):
        frame = ctk.CTkFrame(master, corner_radius=10, border_width=2, border_color=color)
        frame.grid(row=0, column=col, padx=10, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        lbl = ctk.CTkLabel(frame, text=valor, font=ctk.CTkFont(size=24, weight="bold"), text_color=color)
        lbl.pack(pady=(0, 15))
        return lbl

    def cargar_datos(self):
        with SessionLocal() as db:
            # 1. Calcular Dinero en Caja
            txs = db.query(TransaccionFinanciera).all()
            caja = sum([t.monto for t in txs if t.tipo == "Ingreso" or t.categoria == "Capital Inicial"]) - sum([t.monto for t in txs if t.tipo == "Egreso"])
            self.lbl_caja.configure(text=f"$ {caja:,.0f}")

            # 2. Calcular Valor del Inventario (Stock * Costo Unitario)
            valor_inv = db.query(func.sum(Producto.stock_actual * Producto.costo_unitario)).scalar() or 0
            self.lbl_inventario.configure(text=f"$ {valor_inv:,.0f}")

            # 3. Calcular Total de Ventas
            ventas = db.query(func.sum(Venta.total_cobrado)).scalar() or 0
            self.lbl_ventas.configure(text=f"$ {ventas:,.0f}")

            # 4. Llenar tabla de alertas
            for item in self.tree_alertas.get_children(): self.tree_alertas.delete(item)
            stock_bajo = db.query(Producto).filter(Producto.stock_actual <= Producto.stock_minimo).all()
            for p in stock_bajo:
                self.tree_alertas.insert("", "end", values=(p.nombre, p.stock_actual))

            # 5. Generar Gráfico de Top 5 Vendidos
            top_productos = db.query(Producto.nombre, func.sum(DetalleVenta.cantidad).label('total'))\
                              .join(DetalleVenta, Producto.id == DetalleVenta.producto_id)\
                              .group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).limit(5).all()

            self.dibujar_grafico(top_productos)

    def dibujar_grafico(self, datos):
        # Limpiar gráfico anterior si existe
        for widget in self.frame_grafico.winfo_children():
            if isinstance(widget, ctk.CTkLabel): continue
            widget.destroy()

        nombres = [d[0][:15] + "..." if len(d[0]) > 15 else d[0] for d in datos] # Acortar nombres largos
        cantidades = [d[1] for d in datos]

        if not nombres:
            ctk.CTkLabel(self.frame_grafico, text="Aún no hay ventas suficientes para el gráfico.", text_color="gray").pack(pady=50)
            return

        # Configurar figura de Matplotlib adaptada al modo oscuro
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
        
        barras = ax.bar(nombres, cantidades, color='#1f538d')
        
        # Estilos del gráfico
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_color('#2b2b2b')
        ax.set_ylabel('Unidades Vendidas', color='white')
        plt.xticks(rotation=15, ha="right", fontsize=9)
        plt.tight_layout()

        # Integrar gráfico en CustomTkinter
        canvas = FigureCanvasTkAgg(fig, master=self.frame_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)