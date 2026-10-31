import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Venta, Compra, TransaccionFinanciera, DetalleVenta, Producto
from datetime import datetime, timedelta
from sqlalchemy import func

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

class VistaReportes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(self, text="Reportes y Estadísticas", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 5), anchor="w")

        if not HAS_MATPLOTLIB or not HAS_TKCALENDAR:
            ctk.CTkLabel(self, text="⚠️ Faltan librerías. Revisa la instalación.", text_color="#dc3545", font=ctk.CTkFont(weight="bold")).pack(pady=20)
            return

        # --- SISTEMA DE PESTAÑAS ---
        self.tabview = ctk.CTkTabview(self, fg_color="#2b2b2b")
        self.tabview.pack(fill="both", expand=True)

        self.tab_operaciones = self.tabview.add("📊 Rendimiento Operativo (Gráficos)")
        self.tab_patrimonio = self.tabview.add("💰 ¿Dónde está mi dinero? (Patrimonio)")

        self.construir_tab_operaciones()
        self.construir_tab_patrimonio()
        
        self.al_cambiar_periodo()

    def construir_tab_operaciones(self):
        # --- CONTROLES DE FILTRO ---
        frame_filtros = ctk.CTkFrame(self.tab_operaciones, fg_color="transparent")
        frame_filtros.pack(fill="x", pady=(0, 10))

        # Fila 1: Selectores principales
        ctk.CTkLabel(frame_filtros, text="Período:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.combo_periodo = ttk.Combobox(frame_filtros, values=["Diario", "Semanal", "Mensual", "Anual", "Rango Personalizado"], state="readonly", width=18)
        self.combo_periodo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.combo_periodo.set("Mensual")
        self.combo_periodo.bind("<<ComboboxSelected>>", self.al_cambiar_periodo)

        ctk.CTkLabel(frame_filtros, text="Ver ingresos como:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        opciones_metrica = ["Ingresos Brutos (Caja Total)", "Utilidad Bruta (Libre de Costos)", "Utilidad Neta (Libre de Gastos)"]
        self.combo_metrica = ttk.Combobox(frame_filtros, values=opciones_metrica, state="readonly", width=32)
        self.combo_metrica.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.combo_metrica.set(opciones_metrica[0])
        self.combo_metrica.bind("<<ComboboxSelected>>", lambda e: self.generar_reporte())

        ctk.CTkButton(frame_filtros, text="📊 Actualizar", fg_color="#17a2b8", hover_color="#138496", command=self.generar_reporte).grid(row=0, column=4, padx=20, pady=5)

        # Fila 2: Controles dinámicos de fecha
        self.frame_fechas = ctk.CTkFrame(frame_filtros, fg_color="transparent")
        self.frame_fechas.grid(row=1, column=0, columnspan=5, padx=10, pady=(0, 5), sticky="w")

        self.lbl_dia = ctk.CTkLabel(self.frame_fechas, text="Día:")
        self.entry_dia = DateEntry(self.frame_fechas, width=12, background='#1f538d', foreground='white', borderwidth=0, date_pattern='yyyy-mm-dd')
        self.entry_dia.bind("<<DateEntrySelected>>", lambda e: self.generar_reporte())

        self.lbl_semana = ctk.CTkLabel(self.frame_fechas, text="* Calculando la semana en curso (Lunes a Domingo)...", text_color="#a8a8a8")

        self.lbl_desde = ctk.CTkLabel(self.frame_fechas, text="Desde:")
        self.entry_desde = DateEntry(self.frame_fechas, width=12, background='#1f538d', foreground='white', borderwidth=0, date_pattern='yyyy-mm-dd')
        self.entry_desde.bind("<<DateEntrySelected>>", lambda e: self.generar_reporte())
        
        self.lbl_hasta = ctk.CTkLabel(self.frame_fechas, text="Hasta:")
        self.entry_hasta = DateEntry(self.frame_fechas, width=12, background='#1f538d', foreground='white', borderwidth=0, date_pattern='yyyy-mm-dd')
        self.entry_hasta.bind("<<DateEntrySelected>>", lambda e: self.generar_reporte())

        self.lbl_ano = ctk.CTkLabel(self.frame_fechas, text="Año:")
        self.combo_ano = ttk.Combobox(self.frame_fechas, values=[str(a) for a in range(2023, 2031)], state="readonly", width=10)
        self.combo_ano.set(str(datetime.now().year))
        self.combo_ano.bind("<<ComboboxSelected>>", lambda e: self.generar_reporte())

        # --- TARJETAS DE RESUMEN ---
        self.frame_tarjetas = ctk.CTkFrame(self.tab_operaciones, fg_color="transparent")
        self.frame_tarjetas.pack(fill="x", pady=5)
        # Ahora son 4 columnas para incluir el costo
        self.frame_tarjetas.columnconfigure((0,1,2,3), weight=1)

        self.lbl_tit_ventas, self.lbl_val_ventas = self.crear_tarjeta(self.frame_tarjetas, "Ingresos Brutos (Caja)", "$ 0", 0, "#28a745")
        self.lbl_tit_costos, self.lbl_val_costos = self.crear_tarjeta(self.frame_tarjetas, "Costo de lo Vendido", "$ 0", 1, "#fd7e14")
        self.lbl_tit_compras, self.lbl_val_compras = self.crear_tarjeta(self.frame_tarjetas, "Inversión en Compras", "$ 0", 2, "#ffc107")
        self.lbl_tit_gastos, self.lbl_val_gastos = self.crear_tarjeta(self.frame_tarjetas, "Gastos y Mermas", "$ 0", 3, "#dc3545")

        # --- AREA DE GRAFICOS ---
        self.frame_graficos = ctk.CTkFrame(self.tab_operaciones, corner_radius=10, fg_color="#333333")
        self.frame_graficos.pack(fill="both", expand=True, pady=5)
        self.canvas = None

    def construir_tab_patrimonio(self):
        ctk.CTkLabel(self.tab_patrimonio, text="Estado General: Todo lo que tu negocio tiene a su nombre hoy (En Tiempo Real).", 
                     font=ctk.CTkFont(size=14, slant="italic"), text_color="#a8a8a8").pack(pady=(5, 15))

        frame_columnas = ctk.CTkFrame(self.tab_patrimonio, fg_color="transparent")
        frame_columnas.pack(fill="both", expand=True)
        frame_columnas.columnconfigure(0, weight=1)
        frame_columnas.columnconfigure(1, weight=1)

        frame_izq = ctk.CTkFrame(frame_columnas, corner_radius=10, fg_color="#333333")
        frame_izq.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_izq, text="¿De dónde salió el valor?", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.lbl_pat_capital = ctk.CTkLabel(frame_izq, text="Capital Inicial: $ 0", font=ctk.CTkFont(size=16))
        self.lbl_pat_capital.pack(pady=10)
        self.lbl_pat_ganancia = ctk.CTkLabel(frame_izq, text="Ganancia Neta (Global): $ 0", font=ctk.CTkFont(size=16), text_color="#28a745")
        self.lbl_pat_ganancia.pack(pady=10)
        
        ctk.CTkFrame(frame_izq, height=2, fg_color="#555555").pack(fill="x", padx=40, pady=15)
        
        self.lbl_pat_total_origen = ctk.CTkLabel(frame_izq, text="TOTAL PATRIMONIO: $ 0", font=ctk.CTkFont(size=20, weight="bold"), text_color="#17a2b8")
        self.lbl_pat_total_origen.pack(pady=15)

        frame_der = ctk.CTkFrame(frame_columnas, corner_radius=10, fg_color="#333333")
        frame_der.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")

        ctk.CTkLabel(frame_der, text="¿Dónde está físicamente hoy?", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        self.lbl_pat_caja = ctk.CTkLabel(frame_der, text="Dinero en Caja y Bancos: $ 0", font=ctk.CTkFont(size=16))
        self.lbl_pat_caja.pack(pady=10)
        self.lbl_pat_cxc = ctk.CTkLabel(frame_der, text="Cuentas por Cobrar (Clientes): $ 0", font=ctk.CTkFont(size=16), text_color="#ffc107")
        self.lbl_pat_cxc.pack(pady=10)
        self.lbl_pat_inv = ctk.CTkLabel(frame_der, text="Mercancía en Inventario: $ 0", font=ctk.CTkFont(size=16))
        self.lbl_pat_inv.pack(pady=10)

        ctk.CTkFrame(frame_der, height=2, fg_color="#555555").pack(fill="x", padx=40, pady=15)
        
        self.lbl_pat_total_destino = ctk.CTkLabel(frame_der, text="TOTAL SUMA EXACTA: $ 0", font=ctk.CTkFont(size=20, weight="bold"), text_color="#17a2b8")
        self.lbl_pat_total_destino.pack(pady=15)

    def crear_tarjeta(self, parent, titulo, valor, col, color):
        frame = ctk.CTkFrame(parent, corner_radius=10, fg_color="#333333", border_width=2, border_color=color)
        frame.grid(row=0, column=col, padx=10, sticky="nsew")
        lbl_titulo = ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#a8a8a8")
        lbl_titulo.pack(pady=(15, 5))
        lbl_valor = ctk.CTkLabel(frame, text=valor, font=ctk.CTkFont(size=20, weight="bold"), text_color=color)
        lbl_valor.pack(pady=(0, 15))
        return lbl_titulo, lbl_valor

    def al_cambiar_periodo(self, event=None):
        for widget in self.frame_fechas.winfo_children():
            widget.grid_forget()

        periodo = self.combo_periodo.get()
        if periodo == "Diario":
            self.lbl_dia.grid(row=0, column=0, padx=5)
            self.entry_dia.grid(row=0, column=1, padx=5)
        elif periodo == "Semanal":
            self.lbl_semana.grid(row=0, column=0, padx=5)
        elif periodo in ["Mensual", "Rango Personalizado"]:
            self.lbl_desde.grid(row=0, column=0, padx=5)
            self.entry_desde.grid(row=0, column=1, padx=5)
            self.lbl_hasta.grid(row=0, column=2, padx=5)
            self.entry_hasta.grid(row=0, column=3, padx=5)
        elif periodo == "Anual":
            self.lbl_ano.grid(row=0, column=0, padx=5)
            self.combo_ano.grid(row=0, column=1, padx=5)
            
        self.generar_reporte()
        self.actualizar_patrimonio()

    def actualizar_patrimonio(self):
        with SessionLocal() as db:
            ingresos = db.query(func.sum(TransaccionFinanciera.monto)).filter_by(tipo="Ingreso").scalar() or 0
            egresos = db.query(func.sum(TransaccionFinanciera.monto)).filter_by(tipo="Egreso").scalar() or 0
            caja = ingresos - egresos

            cxc = db.query(func.sum(Venta.saldo_pendiente)).scalar() or 0

            productos = db.query(Producto).all()
            inventario = sum((p.stock_actual * p.costo_unitario) for p in productos if p.stock_actual > 0)

            patrimonio_total = caja + cxc + inventario
            capital_inicial = db.query(func.sum(TransaccionFinanciera.monto)).filter_by(categoria="Capital Inicial").scalar() or 0
            ganancia_neta_global = patrimonio_total - capital_inicial

        self.lbl_pat_capital.configure(text=f"Capital Inicial: $ {capital_inicial:,.0f}")
        self.lbl_pat_ganancia.configure(text=f"Ganancia Neta (Global): $ {ganancia_neta_global:,.0f}")
        self.lbl_pat_total_origen.configure(text=f"TOTAL PATRIMONIO: $ {patrimonio_total:,.0f}")

        self.lbl_pat_caja.configure(text=f"Dinero en Caja y Bancos: $ {caja:,.0f}")
        self.lbl_pat_cxc.configure(text=f"Cuentas por Cobrar (Clientes): $ {cxc:,.0f}")
        self.lbl_pat_inv.configure(text=f"Mercancía en Inventario: $ {inventario:,.0f}")
        self.lbl_pat_total_destino.configure(text=f"TOTAL SUMA EXACTA: $ {patrimonio_total:,.0f}")

    def generar_reporte(self):
        periodo = self.combo_periodo.get()
        hoy = datetime.now()

        try:
            if periodo == "Diario":
                d_dia = self.entry_dia.get_date()
                fecha_inicio = datetime.combine(d_dia, datetime.min.time())
                fecha_fin = datetime.combine(d_dia, datetime.max.time())
            elif periodo == "Semanal":
                lunes = hoy - timedelta(days=hoy.weekday())
                domingo = lunes + timedelta(days=6)
                fecha_inicio = lunes.replace(hour=0, minute=0, second=0)
                fecha_fin = domingo.replace(hour=23, minute=59, second=59)
            elif periodo in ["Mensual", "Rango Personalizado"]:
                d_desde = self.entry_desde.get_date()
                d_hasta = self.entry_hasta.get_date()
                fecha_inicio = datetime.combine(d_desde, datetime.min.time())
                fecha_fin = datetime.combine(d_hasta, datetime.max.time())
            elif periodo == "Anual":
                ano = int(self.combo_ano.get())
                fecha_inicio = datetime(ano, 1, 1, 0, 0, 0)
                fecha_fin = datetime(ano, 12, 31, 23, 59, 59)
        except Exception:
            return

        with SessionLocal() as db:
            ventas_brutas = db.query(func.sum(Venta.total_cobrado)).filter(Venta.fecha >= fecha_inicio, Venta.fecha <= fecha_fin).scalar() or 0
            costo_ventas = db.query(
                func.sum(DetalleVenta.cantidad * DetalleVenta.costo_unitario_historico)
            ).join(Venta, Venta.id == DetalleVenta.venta_id).filter(Venta.fecha >= fecha_inicio, Venta.fecha <= fecha_fin).scalar() or 0
            compras = db.query(func.sum(Compra.total)).filter(Compra.fecha >= fecha_inicio, Compra.fecha <= fecha_fin).scalar() or 0
            gastos = db.query(func.sum(TransaccionFinanciera.monto)).filter(
                TransaccionFinanciera.tipo == "Egreso", TransaccionFinanciera.categoria != "Pago Compra y Envío",
                TransaccionFinanciera.fecha >= fecha_inicio, TransaccionFinanciera.fecha <= fecha_fin
            ).scalar() or 0

            top_productos = db.query(
                Producto.nombre, Producto.color, func.sum(DetalleVenta.cantidad).label('total_vendido')
            ).join(DetalleVenta, Producto.id == DetalleVenta.producto_id).join(Venta, Venta.id == DetalleVenta.venta_id)\
             .filter(Venta.fecha >= fecha_inicio, Venta.fecha <= fecha_fin).group_by(Producto.id).order_by(func.sum(DetalleVenta.cantidad).desc()).limit(5).all()

        metrica = self.combo_metrica.get()
        if "Brutos" in metrica:
            ventas_mostrar = ventas_brutas
            titulo_ventas = "Ingresos Brutos (Caja)"
        elif "Utilidad Bruta" in metrica:
            ventas_mostrar = ventas_brutas - costo_ventas
            titulo_ventas = "Utilidad Bruta (Sin Costos)"
        else:
            ventas_mostrar = ventas_brutas - costo_ventas - gastos
            titulo_ventas = "Utilidad Neta (Ganancia Real)"

        self.lbl_tit_ventas.configure(text=titulo_ventas)
        self.lbl_val_ventas.configure(text=f"$ {ventas_mostrar:,.0f}")
        
        # Muestra el costo de ventas permanentemente
        self.lbl_val_costos.configure(text=f"$ {costo_ventas:,.0f}")
        
        self.lbl_val_compras.configure(text=f"$ {compras:,.0f}")
        self.lbl_val_gastos.configure(text=f"$ {gastos:,.0f}")

        self.dibujar_graficos(ventas_mostrar, compras, gastos, top_productos, titulo_ventas)

    def dibujar_graficos(self, ventas, compras, gastos, top_productos, titulo_ventas):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor='#333333')

        categorias = [titulo_ventas.split(' (')[0], 'Compras', 'Gastos/Merma']
        valores = [ventas, compras, gastos]
        colores = ['#28a745', '#ffc107', '#dc3545']

        bars = ax1.bar(categorias, valores, color=colores)
        ax1.set_title('Balance Financiero del Período', color='white', pad=15, fontsize=12, fontweight='bold')
        ax1.set_facecolor('#333333')
        ax1.tick_params(colors='white')
        for spine in ax1.spines.values():
            spine.set_color('#555555')
            
        for bar in bars:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, yval, f'${yval:,.0f}', ha='center', va='bottom', color='white', fontsize=9)

        ax2.set_facecolor('#333333')
        ax2.tick_params(colors='white')
        for spine in ax2.spines.values():
            spine.set_color('#555555')

        if top_productos:
            nombres = [f"{p.nombre[:15]} ({p.color})" if p.color else p.nombre[:15] for p in top_productos]
            cantidades = [p.total_vendido for p in top_productos]
            ax2.barh(nombres, cantidades, color='#17a2b8')
            ax2.set_title('Top 5 Productos Vendidos', color='white', pad=15, fontsize=12, fontweight='bold')
            ax2.invert_yaxis() 
        else:
            ax2.text(0.5, 0.5, 'No hay ventas en este período', ha='center', va='center', color='white')
            ax2.axis('off')

        fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(fig, master=self.frame_graficos)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)