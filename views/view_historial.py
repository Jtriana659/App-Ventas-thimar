import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Venta, DetalleVenta, Producto

class VistaHistorial(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self, text="Historial de Ventas y Rentabilidad", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # --- ESTRUCTURA A DOS COLUMNAS ---
        self.frame_izq = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.frame_der = ctk.CTkFrame(self, width=400, corner_radius=10)
        self.frame_der.pack(side="right", fill="y")
        self.frame_der.pack_propagate(False) # Evita que el panel cambie de tamaño

        self.construir_panel_izquierdo()
        self.construir_panel_derecho()
        self.cargar_ventas()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def construir_panel_izquierdo(self):
        ctk.CTkLabel(self.frame_izq, text="Lista de Ventas Realizadas", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(0,10), anchor="w")
        
        self.aplicar_estilo_tabla()
        self.tree_ventas = ttk.Treeview(self.frame_izq, columns=("id", "fecha", "cliente", "total"), show="headings", height=20)
        self.tree_ventas.heading("id", text="N° Venta")
        self.tree_ventas.heading("fecha", text="Fecha")
        self.tree_ventas.heading("cliente", text="Cliente")
        self.tree_ventas.heading("total", text="Total Cobrado")
        
        self.tree_ventas.column("id", width=80, anchor="center")
        self.tree_ventas.column("fecha", width=150)
        self.tree_ventas.column("cliente", width=200)
        self.tree_ventas.column("total", width=120, anchor="e")
        self.tree_ventas.pack(fill="both", expand=True)
        
        # Evento: Al hacer clic en una venta, mostrar resumen
        self.tree_ventas.bind("<<TreeviewSelect>>", self.mostrar_resumen)
        
        ctk.CTkButton(self.frame_izq, text="🔄 Actualizar Lista", command=self.cargar_ventas).pack(pady=10, anchor="w")

    def construir_panel_derecho(self):
        ctk.CTkLabel(self.frame_der, text="Resumen de Venta", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)
        
        # Contenedor de texto dinámico
        self.textbox_resumen = ctk.CTkTextbox(self.frame_der, font=ctk.CTkFont(family="Consolas", size=13), fg_color="transparent")
        self.textbox_resumen.pack(fill="both", expand=True, padx=15, pady=10)
        self.textbox_resumen.insert("0.0", "Selecciona una venta de la tabla\npara ver el desglose de rentabilidad.")
        self.textbox_resumen.configure(state="disabled")

    def cargar_ventas(self):
        for item in self.tree_ventas.get_children(): self.tree_ventas.delete(item)
        with SessionLocal() as db:
            # Traer ventas ordenadas de la más reciente a la más antigua
            ventas = db.query(Venta).order_by(Venta.id.desc()).all()
            for v in ventas:
                fecha_str = v.fecha.strftime("%Y-%m-%d %H:%M")
                self.tree_ventas.insert("", "end", values=(v.id, fecha_str, v.cliente, f"$ {v.total_cobrado:,.0f}"))

    def mostrar_resumen(self, event):
        seleccion = self.tree_ventas.selection()
        if not seleccion: return
        
        id_venta = self.tree_ventas.item(seleccion[0])['values'][0]
        
        with SessionLocal() as db:
            venta = db.query(Venta).filter(Venta.id == id_venta).first()
            if not venta: return
            
            detalles = db.query(DetalleVenta).filter(DetalleVenta.venta_id == venta.id).all()
            
            # --- CÁLCULOS MATEMÁTICOS ---
            costo_total_productos = 0
            texto_articulos = ""
            
            for d in detalles:
                producto = db.query(Producto).get(d.producto_id)
                nombre_prod = producto.nombre if producto else "Producto Eliminado"
                costo_linea = d.cantidad * d.costo_unitario_historico
                costo_total_productos += costo_linea
                
                texto_articulos += f" - {d.cantidad}x {nombre_prod}\n"
                texto_articulos += f"   (Costo: ${d.costo_unitario_historico:,.0f} | Vendido a: ${d.precio_unitario:,.0f})\n"

            # Fórmulas de Rentabilidad
            ingresos_reales = venta.total_cobrado
            egresos_reales = costo_total_productos + venta.gasto_domicilio
            ganancia_neta = ingresos_reales - egresos_reales

            # --- CONSTRUCCIÓN DEL REPORTE VISUAL ---
            reporte = f"=== VENTA N° {venta.id} ===\n"
            reporte += f"Fecha: {venta.fecha.strftime('%Y-%m-%d %H:%M')}\n"
            reporte += f"Cliente: {venta.cliente}\n"
            reporte += f"Modalidad: {venta.tipo_domicilio}\n"
            reporte += "="*30 + "\n\n"
            
            reporte += "1. ARTÍCULOS INVOLUCRADOS:\n"
            reporte += texto_articulos + "\n"
            
            reporte += "2. RESUMEN DE DINERO (INGRESOS):\n"
            reporte += f" + Subtotal Productos : $ {venta.subtotal:,.0f}\n"
            reporte += f" + Cobro por Domicilio: $ {venta.ingreso_domicilio:,.0f}\n"
            reporte += f" ---------------------------------\n"
            reporte += f" TOTAL RECIBIDO       : $ {ingresos_reales:,.0f}\n\n"
            
            reporte += "3. COSTOS DIRECTOS (EGRESOS):\n"
            reporte += f" - Costo de Artículos : $ {costo_total_productos:,.0f}\n"
            reporte += f" - Pago Transportador : $ {venta.gasto_domicilio:,.0f}\n"
            reporte += f" ---------------------------------\n"
            reporte += f" TOTAL GASTADO        : $ {egresos_reales:,.0f}\n\n"
            
            reporte += "="*30 + "\n"
            reporte += f" GANANCIA LIBRE (NETA): $ {ganancia_neta:,.0f}\n"
            reporte += "="*30 + "\n"
            
            if ganancia_neta <= 0:
                reporte += "\n⚠️ ADVERTENCIA: Esta venta no generó\nganancias o dio pérdidas. Revisa\ntus costos de envío o de insumos."

            # Mostrar en pantalla
            self.textbox_resumen.configure(state="normal")
            self.textbox_resumen.delete("0.0", "end")
            self.textbox_resumen.insert("0.0", reporte)
            self.textbox_resumen.configure(state="disabled")