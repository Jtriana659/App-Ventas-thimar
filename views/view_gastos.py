import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Producto, TransaccionFinanciera, MovimientoInventario, TipoMovimiento
import controllers

class VistaGastos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self, text="Gastos Operativos y Mermas (Daños)", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10), anchor="w")

        # --- PARTE SUPERIOR: FORMULARIOS ---
        self.frame_formularios = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_formularios.pack(fill="x", pady=(0, 10))
        
        self.frame_izq = ctk.CTkFrame(self.frame_formularios, corner_radius=10, fg_color="#2b2b2b", border_width=1, border_color="#444444")
        self.frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.frame_der = ctk.CTkFrame(self.frame_formularios, corner_radius=10, fg_color="#2b2b2b", border_width=1, border_color="#444444")
        self.frame_der.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.productos_dict = {}

        self.construir_panel_gastos()
        self.construir_panel_bajas()
        
        # --- PARTE INFERIOR: HISTORIAL ---
        self.construir_panel_historial()
        
        self.cargar_productos_disponibles()
        self.cargar_historial()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def construir_panel_gastos(self):
        ctk.CTkLabel(self.frame_izq, text="💸 Registrar Gasto Operativo", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(self.frame_izq, text="Categoría del Gasto:").pack(anchor="w", padx=30)
        categorias = ["-- Seleccione una categoría --", "Material de Empaque (Cajas, Bolsas)", "Publicidad (Redes Sociales, Tarjetas)", "Papelería / Tintas Impresora", "Servicios (Luz, Internet)", "Mantenimiento Máquinas", "Otro"]
        self.combo_categoria = ctk.CTkOptionMenu(self.frame_izq, width=300, values=categorias)
        self.combo_categoria.pack(padx=30, pady=(0, 10))
        self.combo_categoria.set("-- Seleccione una categoría --")

        ctk.CTkLabel(self.frame_izq, text="Valor Pagado ($):").pack(anchor="w", padx=30)
        self.entry_monto = ctk.CTkEntry(self.frame_izq, width=300)
        self.entry_monto.pack(padx=30, pady=(0, 10))

        ctk.CTkLabel(self.frame_izq, text="Descripción / Observaciones:").pack(anchor="w", padx=30)
        self.entry_obs_gasto = ctk.CTkEntry(self.frame_izq, width=300, placeholder_text="Ej: Compra de 50 cajas para mugs")
        self.entry_obs_gasto.pack(padx=30, pady=(0, 10))

        ctk.CTkButton(self.frame_izq, text="Registrar Gasto", fg_color="#ffc107", text_color="black", hover_color="#e0a800", font=ctk.CTkFont(weight="bold"), command=self.registrar_gasto).pack(side="bottom", padx=30, pady=15, fill="x")

    def construir_panel_bajas(self):
        ctk.CTkLabel(self.frame_der, text="⚠️ Registrar Baja o Daño (Merma)", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(self.frame_der, text="Producto Dañado:").pack(anchor="w", padx=30)
        self.combo_prod = ctk.CTkOptionMenu(self.frame_der, width=300, values=["Cargando..."])
        self.combo_prod.pack(padx=30, pady=(0, 10))

        ctk.CTkLabel(self.frame_der, text="Cantidad:").pack(anchor="w", padx=30)
        self.entry_cant = ctk.CTkEntry(self.frame_der, width=300)
        self.entry_cant.insert(0, "1")
        self.entry_cant.pack(anchor="w", padx=30, pady=(0, 10))

        ctk.CTkLabel(self.frame_der, text="Motivo del Daño:").pack(anchor="w", padx=30)
        self.entry_obs_baja = ctk.CTkEntry(self.frame_der, width=300, placeholder_text="Ej: Se quemó en la plancha / Mug quebrado")
        self.entry_obs_baja.pack(padx=30, pady=(0, 10))

        ctk.CTkLabel(self.frame_der, text="* Esta acción descontará el stock e imputará\nla pérdida del costo en el módulo de Finanzas.", font=ctk.CTkFont(size=11, slant="italic"), text_color="#a8a8a8").pack(anchor="w", padx=30, pady=(0, 5))

        ctk.CTkButton(self.frame_der, text="Registrar Daño", fg_color="#dc3545", hover_color="#c82333", font=ctk.CTkFont(weight="bold"), command=self.registrar_baja).pack(side="bottom", padx=30, pady=15, fill="x")

    def construir_panel_historial(self):
        self.frame_historial = ctk.CTkFrame(self, corner_radius=10)
        self.frame_historial.pack(fill="both", expand=True, pady=(10, 0), ipady=5)

        # Barra superior del historial
        frame_top_historial = ctk.CTkFrame(self.frame_historial, fg_color="transparent")
        frame_top_historial.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(frame_top_historial, text="Historial de Registros", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        # --- BOTÓN ELIMINAR MOVIDO ARRIBA PARA QUE SIEMPRE SE VEA ---
        ctk.CTkButton(frame_top_historial, text="🗑️ Eliminar Seleccionado", fg_color="#dc3545", hover_color="#c82333", font=ctk.CTkFont(weight="bold"), command=self.eliminar_registro).pack(side="left", padx=20)
        
        self.entry_filtro = ctk.CTkEntry(frame_top_historial, width=250, placeholder_text="Filtrar por fecha, categoría...")
        self.entry_filtro.pack(side="right", padx=(10, 0))
        self.entry_filtro.bind("<KeyRelease>", lambda e: self.cargar_historial(self.entry_filtro.get()))
        
        ctk.CTkLabel(frame_top_historial, text="🔍 Buscar:").pack(side="right")

        # Tabla (Añadimos dos columnas ocultas para guardar el ID y el TIPO)
        self.aplicar_estilo_tabla()
        self.tree_hist = ttk.Treeview(self.frame_historial, columns=("id_db", "tipo_db", "fecha", "tipo", "concepto", "detalle", "valor"), show="headings", height=8)
        
        self.tree_hist.heading("id_db", text="ID")
        self.tree_hist.heading("tipo_db", text="Tipo DB")
        self.tree_hist.heading("fecha", text="Fecha")
        self.tree_hist.heading("tipo", text="Tipo")
        self.tree_hist.heading("concepto", text="Categoría / Producto")
        self.tree_hist.heading("detalle", text="Observaciones / Motivo")
        self.tree_hist.heading("valor", text="Monto / Cantidad")
        
        # Ocultamos las columnas técnicas
        self.tree_hist.column("id_db", width=0, stretch=False)
        self.tree_hist.column("tipo_db", width=0, stretch=False)
        
        self.tree_hist.column("fecha", width=120, anchor="center")
        self.tree_hist.column("tipo", width=100, anchor="center")
        self.tree_hist.column("concepto", width=180)
        self.tree_hist.column("detalle", width=250)
        self.tree_hist.column("valor", width=100, anchor="center")
        
        self.tree_hist.pack(fill="both", expand=True, padx=15, pady=(0, 10))

    def cargar_productos_disponibles(self):
        with SessionLocal() as db:
            productos = db.query(Producto).filter(Producto.stock_actual > 0).all()
            self.productos_dict = {f"{p.sku} - {p.nombre} (Stock: {p.stock_actual})": p.id for p in productos}
            
            if self.productos_dict:
                valores_dropdown = ["-- Seleccione un producto --"] + list(self.productos_dict.keys())
                self.combo_prod.configure(values=valores_dropdown)
                self.combo_prod.set("-- Seleccione un producto --")
            else:
                self.combo_prod.configure(values=["No hay productos con stock"])
                self.combo_prod.set("No hay productos con stock")

    def cargar_historial(self, filtro_texto=""):
        for item in self.tree_hist.get_children(): self.tree_hist.delete(item)
        filtro_texto = filtro_texto.lower()
        
        registros = []
        with SessionLocal() as db:
            gastos = db.query(TransaccionFinanciera).filter(TransaccionFinanciera.referencia_id == 0, TransaccionFinanciera.tipo == "Egreso").all()
            for g in gastos:
                registros.append({
                    "id_db": g.id,
                    "tipo_db": "GASTO",
                    "fecha_obj": g.fecha,
                    "fecha": g.fecha.strftime("%Y-%m-%d %H:%M"),
                    "tipo": "Gasto",
                    "concepto": g.categoria,
                    "detalle": g.observaciones or "N/A",
                    "valor": f"$ {g.monto:,.0f}"
                })
            
            danos = db.query(MovimientoInventario).filter(MovimientoInventario.tipo == TipoMovimiento.AJUSTE).all()
            for d in danos:
                prod = db.query(Producto).get(d.producto_id)
                nombre_prod = prod.nombre if prod else "Producto Eliminado"
                registros.append({
                    "id_db": d.id,
                    "tipo_db": "DANO",
                    "fecha_obj": d.fecha,
                    "fecha": d.fecha.strftime("%Y-%m-%d %H:%M"),
                    "tipo": "Daño/Merma",
                    "concepto": nombre_prod,
                    "detalle": d.observaciones or "N/A",
                    "valor": f"{abs(d.cantidad)} und(s)"
                })
        
        registros.sort(key=lambda x: x["fecha_obj"], reverse=True)
        
        for r in registros:
            texto_fila = f"{r['fecha']} {r['tipo']} {r['concepto']} {r['detalle']} {r['valor']}".lower()
            if filtro_texto in texto_fila:
                self.tree_hist.insert("", "end", values=(r["id_db"], r["tipo_db"], r["fecha"], r["tipo"], r["concepto"], r["detalle"], r["valor"]))

    def registrar_gasto(self):
        categoria = self.combo_categoria.get()
        if categoria == "-- Seleccione una categoría --":
            return print("Por favor seleccione una categoría de gasto")

        try: monto = float(self.entry_monto.get())
        except: return print("Monto inválido")
        
        exito, msg = controllers.registrar_gasto_operativo(
            categoria=categoria,
            monto=monto,
            observaciones=self.entry_obs_gasto.get()
        )
        
        if exito:
            self.entry_monto.delete(0, 'end')
            self.entry_obs_gasto.delete(0, 'end')
            self.combo_categoria.set("-- Seleccione una categoría --")
            self.cargar_historial()
            print("Gasto operativo registrado")

    def registrar_baja(self):
        seleccion = self.combo_prod.get()
        if seleccion == "-- Seleccione un producto --" or seleccion not in self.productos_dict: 
            return print("Seleccione un producto válido para reportar daño")
            
        id_prod = self.productos_dict[seleccion]
        
        try: cant = int(self.entry_cant.get())
        except: return print("Cantidad inválida")

        exito, msg = controllers.registrar_baja_inventario(
            producto_id=id_prod,
            cantidad=cant,
            motivo=self.entry_obs_baja.get()
        )
        
        if exito:
            self.entry_cant.delete(0, 'end')
            self.entry_cant.insert(0, "1")
            self.entry_obs_baja.delete(0, 'end')
            self.cargar_productos_disponibles()
            self.cargar_historial()
            print("Daño reportado correctamente")
        else:
            print(f"Error: {msg}")

    def eliminar_registro(self):
        seleccion = self.tree_hist.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona un registro de la tabla para eliminar.")
            return
            
        item = self.tree_hist.item(seleccion[0])
        id_db = int(item['values'][0])
        tipo_db = item['values'][1]
        
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación", 
            "¿Estás seguro de que deseas eliminar este registro?\n\n- Si es un gasto, el dinero regresará a tus cuentas.\n- Si es un daño, el producto regresará al inventario."
        )
        
        if confirmacion:
            exito, msg = controllers.eliminar_registro_gasto_dano(tipo_db, id_db)
            if exito:
                self.cargar_historial()
                self.cargar_productos_disponibles()
                print("Eliminado con éxito.")
            else:
                messagebox.showerror("Error", f"No se pudo eliminar: {msg}")