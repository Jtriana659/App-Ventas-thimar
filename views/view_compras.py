import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Producto, Proveedor, Compra, DetalleCompra, MovimientoInventario, TipoMovimiento, TransaccionFinanciera
from datetime import datetime

class VistaCompras(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.carrito_compras = [] 
        self.productos_dict = {} 
        self.proveedores_dict = {}

        ctk.CTkLabel(self, text="Registro de Compras e Insumos", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10), anchor="w")

        self.frame_izq = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.frame_der = ctk.CTkFrame(self, width=350, corner_radius=10)
        self.frame_der.pack(side="right", fill="y")

        self.construir_panel_izquierdo()
        self.construir_panel_derecho()
        self.cargar_datos_desplegables()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def construir_panel_izquierdo(self):
        frame_agregar = ctk.CTkFrame(self.frame_izq, corner_radius=10)
        frame_agregar.pack(fill="x", pady=(0, 10), ipady=10)

        # --- FILA 1: Producto (Ocupa todo el ancho) ---
        ctk.CTkLabel(frame_agregar, text="Producto/Insumo:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_prod = ttk.Combobox(frame_agregar, width=65, values=["Cargando..."], state="readonly")
        self.combo_prod.grid(row=0, column=1, columnspan=5, padx=10, pady=10, sticky="w")

        # --- FILA 2: Cantidad, Costo y Botón ---
        ctk.CTkLabel(frame_agregar, text="Cant:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_cant = ctk.CTkEntry(frame_agregar, width=70)
        self.entry_cant.insert(0, "1")
        self.entry_cant.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        ctk.CTkLabel(frame_agregar, text="Costo Unit ($):").grid(row=1, column=2, padx=10, pady=10, sticky="w")
        self.entry_costo = ctk.CTkEntry(frame_agregar, width=100)
        self.entry_costo.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        ctk.CTkButton(frame_agregar, text="➕ Agregar", command=self.agregar_al_carrito).grid(row=1, column=4, padx=20, pady=10)

        self.aplicar_estilo_tabla()
        self.tree_carrito = ttk.Treeview(self.frame_izq, columns=("id", "nombre", "cant", "costo", "sub"), show="headings", height=10)
        self.tree_carrito.heading("id", text="ID")
        self.tree_carrito.heading("nombre", text="Artículo")
        self.tree_carrito.heading("cant", text="Cant.")
        self.tree_carrito.heading("costo", text="Costo Unit.")
        self.tree_carrito.heading("sub", text="Subtotal")
        self.tree_carrito.column("id", width=0, stretch=False)
        self.tree_carrito.column("cant", width=50, anchor="center")
        self.tree_carrito.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.frame_izq, text="🗑️ Quitar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.quitar_del_carrito).pack(pady=10, anchor="w")

    def construir_panel_derecho(self):
        ctk.CTkLabel(self.frame_der, text="Resumen de Compra", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(self.frame_der, text="Proveedor:").pack(anchor="w", padx=20)
        self.combo_prov = ctk.CTkComboBox(self.frame_der, width=280, values=["Cargando..."], state="readonly")
        self.combo_prov.pack(padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_der, text="¿Quién paga el envío?").pack(anchor="w", padx=20)
        self.combo_envio = ctk.CTkComboBox(self.frame_der, width=280, values=["1. Envío Gratis / Incluido", "2. Yo pago el envío extra"], command=self.actualizar_totales, state="readonly")
        self.combo_envio.pack(padx=20, pady=(0, 10))

        self.frame_valores = ctk.CTkFrame(self.frame_der, fg_color="transparent")
        self.frame_valores.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self.frame_valores, text="Costo del Envío ($):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_costo_envio = ctk.CTkEntry(self.frame_valores, width=120)
        self.entry_costo_envio.grid(row=0, column=1, padx=10, pady=2)
        self.entry_costo_envio.insert(0, "0")
        self.entry_costo_envio.bind("<KeyRelease>", self.actualizar_totales)
        self.entry_costo_envio.configure(state="disabled")

        ctk.CTkFrame(self.frame_der, height=2, fg_color="gray").pack(fill="x", padx=20, pady=15)

        self.lbl_subtotal = ctk.CTkLabel(self.frame_der, text="Costo Artículos: $ 0", font=ctk.CTkFont(size=14))
        self.lbl_subtotal.pack(anchor="e", padx=20)
        
        self.lbl_total_pagar = ctk.CTkLabel(self.frame_der, text="TOTAL A PAGAR: $ 0", font=ctk.CTkFont(size=18, weight="bold"), text_color="#dc3545")
        self.lbl_total_pagar.pack(anchor="e", padx=20, pady=10)

        ctk.CTkButton(self.frame_der, text="✅ Confirmar y Pagar", height=40, font=ctk.CTkFont(weight="bold"), command=self.confirmar_compra).pack(padx=20, pady=10, fill="x")

    def cargar_datos_desplegables(self):
        with SessionLocal() as db:
            productos = db.query(Producto).all()
            if productos:
                self.productos_dict = {f"{p.sku} - {p.nombre} (Color: {p.color or 'N/A'})": p.id for p in productos}
                self.combo_prod.configure(values=list(self.productos_dict.keys()))
                self.combo_prod.set(list(self.productos_dict.keys())[0])
            else:
                self.combo_prod.configure(values=["Sin productos"])

            proveedores = db.query(Proveedor).all()
            if proveedores:
                self.proveedores_dict = {p.nombre: p.id for p in proveedores}
                self.combo_prov.configure(values=list(self.proveedores_dict.keys()))
                self.combo_prov.set(list(self.proveedores_dict.keys())[0])
            else:
                self.combo_prov.configure(values=["Sin proveedores"])

    def agregar_al_carrito(self):
        seleccion = self.combo_prod.get()
        if seleccion not in self.productos_dict: return
        id_prod = self.productos_dict[seleccion]
        nombre_prod = seleccion.split(" - ", 1)[1]
        
        try:
            cant = int(self.entry_cant.get())
            costo = float(self.entry_costo.get())
            if cant <= 0 or costo < 0: raise ValueError
        except:
            print("Datos inválidos")
            return

        self.carrito_compras.append({
            'producto_id': id_prod, 'nombre': nombre_prod, 'cantidad': cant,
            'costo_unitario': costo, 'subtotal': cant * costo
        })

        self.actualizar_tabla_carrito()
        self.entry_cant.delete(0, 'end'); self.entry_cant.insert(0, "1")
        self.entry_costo.delete(0, 'end')

    def quitar_del_carrito(self):
        seleccion = self.tree_carrito.selection()
        if not seleccion: return
        id_prod = int(self.tree_carrito.item(seleccion[0])['values'][0])
        self.carrito_compras = [item for item in self.carrito_compras if item['producto_id'] != id_prod]
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for item in self.tree_carrito.get_children(): self.tree_carrito.delete(item)
        for item in self.carrito_compras:
            self.tree_carrito.insert("", "end", values=(item['producto_id'], item['nombre'], item['cantidad'], f"$ {item['costo_unitario']:,.0f}", f"$ {item['subtotal']:,.0f}"))
        self.actualizar_totales()

    def actualizar_totales(self, event=None):
        subtotal = sum(item['subtotal'] for item in self.carrito_compras)
        
        if "Yo pago" in self.combo_envio.get():
            self.entry_costo_envio.configure(state="normal")
            try: costo_envio = float(self.entry_costo_envio.get() or 0)
            except: costo_envio = 0
        else:
            self.entry_costo_envio.delete(0, 'end')
            self.entry_costo_envio.insert(0, "0")
            self.entry_costo_envio.configure(state="disabled")
            costo_envio = 0

        total = subtotal + costo_envio
        self.lbl_subtotal.configure(text=f"Costo Artículos: $ {subtotal:,.0f}")
        self.lbl_total_pagar.configure(text=f"TOTAL A PAGAR: $ {total:,.0f}")

    def confirmar_compra(self):
        if not self.carrito_compras: return
        prov_nombre = self.combo_prov.get()
        if prov_nombre not in self.proveedores_dict: return
        prov_id = self.proveedores_dict[prov_nombre]

        subtotal = sum(item['subtotal'] for item in self.carrito_compras)
        try: costo_envio = float(self.entry_costo_envio.get() or 0) if "Yo pago" in self.combo_envio.get() else 0
        except: costo_envio = 0
        total = subtotal + costo_envio

        with SessionLocal() as db:
            compra = Compra(proveedor_id=prov_id, subtotal=subtotal, costo_envio=costo_envio, total=total, estado_pago="Pagado", estado_recepcion="Recibido", metodo_pago="Caja/Bancos")
            db.add(compra)
            db.flush() 

            tx_egreso = TransaccionFinanciera(tipo="Egreso", categoria="Pago Compra y Envío", monto=total, referencia_id=compra.id, observaciones=f"Compra a {prov_nombre}")
            db.add(tx_egreso)

            for item in self.carrito_compras:
                det = DetalleCompra(compra_id=compra.id, producto_id=item['producto_id'], cantidad=item['cantidad'], costo_unitario_base=item['costo_unitario'])
                db.add(det)

                prod = db.query(Producto).get(item['producto_id'])
                prod.stock_actual += item['cantidad']
                prod.costo_unitario = item['costo_unitario'] 
                
                mov = MovimientoInventario(producto_id=prod.id, tipo=TipoMovimiento.ENTRADA_COMPRA, cantidad=item['cantidad'], observaciones=f"Compra #{compra.id}")
                db.add(mov)

            db.commit()
        
        self.carrito_compras = []
        self.actualizar_tabla_carrito()
        print("Compra registrada exitosamente.")