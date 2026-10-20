import customtkinter as ctk
from tkinter import ttk
from database import SessionLocal
from models import Producto
import controllers

class VistaVentas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.carrito = [] 
        self.productos_dict = {} 

        ctk.CTkLabel(self, text="Punto de Venta (POS)", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 10), anchor="w")

        self.frame_izq = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.frame_der = ctk.CTkFrame(self, width=350, corner_radius=10)
        self.frame_der.pack(side="right", fill="y")

        self.construir_panel_izquierdo()
        self.construir_panel_derecho()
        self.cargar_productos_disponibles()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def construir_panel_izquierdo(self):
        frame_agregar = ctk.CTkFrame(self.frame_izq, corner_radius=10)
        frame_agregar.pack(fill="x", pady=(0, 10), ipady=10)

        # --- FILA 1: Producto ---
        ctk.CTkLabel(frame_agregar, text="Producto:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_prod = ctk.CTkComboBox(frame_agregar, width=400, values=["Cargando..."], command=self.al_seleccionar_producto, state="readonly")
        self.combo_prod.grid(row=0, column=1, columnspan=4, padx=10, pady=10, sticky="w")

        # --- FILA 2: Precio, Cantidad y Botón ---
        ctk.CTkLabel(frame_agregar, text="Precio Venta ($):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_precio = ctk.CTkEntry(frame_agregar, width=100)
        self.entry_precio.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(frame_agregar, text="Cant:").grid(row=1, column=2, padx=10, pady=10, sticky="w")
        self.entry_cant = ctk.CTkEntry(frame_agregar, width=70)
        self.entry_cant.insert(0, "1")
        self.entry_cant.grid(row=1, column=3, padx=10, pady=10, sticky="w")

        ctk.CTkButton(frame_agregar, text="➕ Agregar", command=self.agregar_al_carrito).grid(row=1, column=4, padx=20, pady=10)

        self.aplicar_estilo_tabla()
        self.tree_carrito = ttk.Treeview(self.frame_izq, columns=("id", "nombre", "cant", "precio", "sub"), show="headings", height=10)
        self.tree_carrito.heading("id", text="ID")
        self.tree_carrito.heading("nombre", text="Producto")
        self.tree_carrito.heading("cant", text="Cant.")
        self.tree_carrito.heading("precio", text="Precio Unit.")
        self.tree_carrito.heading("sub", text="Subtotal")
        self.tree_carrito.column("id", width=0, stretch=False)
        self.tree_carrito.column("cant", width=50, anchor="center")
        self.tree_carrito.pack(fill="both", expand=True)
        
        ctk.CTkButton(self.frame_izq, text="🗑️ Quitar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.quitar_del_carrito).pack(pady=10, anchor="w")

    def construir_panel_derecho(self):
        ctk.CTkLabel(self.frame_der, text="Resumen de Venta", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        ctk.CTkLabel(self.frame_der, text="Cliente:").pack(anchor="w", padx=20)
        self.entry_cliente = ctk.CTkEntry(self.frame_der, width=280)
        self.entry_cliente.pack(padx=20, pady=(0, 15))

        ctk.CTkLabel(self.frame_der, text="Tipo de Entrega:").pack(anchor="w", padx=20)
        opciones_dom = ["1. Cliente recoge", "2. Envío gratis (Asumido por el negocio)", "3. Cliente le paga directo al domiciliario"]
        self.combo_domicilio = ctk.CTkComboBox(self.frame_der, width=280, values=opciones_dom, command=self.actualizar_ui_domicilio, state="readonly")
        self.combo_domicilio.pack(padx=20, pady=(0, 10))

        self.frame_valores_dom = ctk.CTkFrame(self.frame_der, fg_color="transparent")
        ctk.CTkLabel(self.frame_valores_dom, text="Dinero que sacas para pagarle:").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_valor_domicilio = ctk.CTkEntry(self.frame_valores_dom, width=100)
        self.entry_valor_domicilio.grid(row=0, column=1, padx=10, pady=2)
        self.entry_valor_domicilio.insert(0, "0")
        self.frame_valores_dom.pack_forget() 

        ctk.CTkFrame(self.frame_der, height=2, fg_color="gray").pack(fill="x", padx=20, pady=5)

        self.lbl_subtotal = ctk.CTkLabel(self.frame_der, text="Subtotal Prod: $ 0", font=ctk.CTkFont(size=14))
        self.lbl_subtotal.pack(anchor="e", padx=20)
        
        self.lbl_total_cobrar = ctk.CTkLabel(self.frame_der, text="TOTAL A COBRAR: $ 0", font=ctk.CTkFont(size=18, weight="bold"), text_color="#28a745")
        self.lbl_total_cobrar.pack(anchor="e", padx=20, pady=5)

        ctk.CTkLabel(self.frame_der, text="Estado de Pago:").pack(anchor="w", padx=20)
        self.combo_estado_pago = ctk.CTkComboBox(self.frame_der, width=280, values=["Pagado Completo", "Abono / Anticipo"], command=self.toggle_abono, state="readonly")
        self.combo_estado_pago.pack(padx=20, pady=(0, 10))

        self.frame_abono = ctk.CTkFrame(self.frame_der, fg_color="transparent")
        ctk.CTkLabel(self.frame_abono, text="Valor Abonado ($):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_abono = ctk.CTkEntry(self.frame_abono, width=120)
        self.entry_abono.grid(row=0, column=1, padx=10, pady=2)
        self.entry_abono.insert(0, "0")
        ctk.CTkLabel(self.frame_abono, text="💡 Dinero que el cliente te entrega HOY (Anticipo).", font=ctk.CTkFont(size=12, slant="italic"), text_color="#a8a8a8").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0,5))
        
        ctk.CTkLabel(self.frame_der, text="Método de Pago:").pack(anchor="w", padx=20)
        self.combo_pago = ctk.CTkComboBox(self.frame_der, width=280, values=["Efectivo", "Nequi", "Daviplata", "Transferencia"], state="readonly")
        self.combo_pago.pack(padx=20, pady=(0, 10))

        ctk.CTkButton(self.frame_der, text="✅ Confirmar Venta", height=40, font=ctk.CTkFont(weight="bold"), command=self.confirmar_venta).pack(padx=20, pady=10, fill="x")

    def al_seleccionar_producto(self, seleccion):
        if seleccion in self.productos_dict:
            prod = self.productos_dict[seleccion]
            self.entry_precio.delete(0, 'end')
            self.entry_precio.insert(0, str(int(prod.precio_venta)))

    def actualizar_ui_domicilio(self, seleccion):
        if "Envío gratis" in seleccion:
            self.frame_valores_dom.pack(fill="x", padx=20, pady=5, after=self.combo_domicilio)
        else:
            self.frame_valores_dom.pack_forget()
            self.entry_valor_domicilio.delete(0, 'end')
            self.entry_valor_domicilio.insert(0, "0")

    def toggle_abono(self, seleccion):
        if seleccion == "Abono / Anticipo":
            self.frame_abono.pack(fill="x", padx=20, pady=5, after=self.combo_estado_pago)
        else:
            self.frame_abono.pack_forget()
            self.entry_abono.delete(0, 'end')
            self.entry_abono.insert(0, "0")

    def cargar_productos_disponibles(self):
        with SessionLocal() as db:
            productos = db.query(Producto).filter(Producto.stock_actual > 0).all()
            self.productos_dict = {f"{p.sku} - {p.nombre} (Color: {p.color or 'N/A'})": p for p in productos}
            
            if self.productos_dict:
                opciones = list(self.productos_dict.keys())
                self.combo_prod.configure(values=opciones)
                self.combo_prod.set(opciones[0])
                self.al_seleccionar_producto(opciones[0])
            else:
                self.combo_prod.configure(values=["No hay productos con stock"])
                self.combo_prod.set("No hay productos con stock")
                self.entry_precio.delete(0, 'end')

    def agregar_al_carrito(self):
        seleccion = self.combo_prod.get()
        if seleccion not in self.productos_dict: return
        
        prod = self.productos_dict[seleccion]
        
        try: cant = int(self.entry_cant.get())
        except: return print("Cantidad inválida")

        try: precio_custom = float(self.entry_precio.get())
        except: return print("Precio inválido")

        if cant > prod.stock_actual:
            return print("Stock insuficiente")

        encontrado = False
        for item in self.carrito:
            if item['producto_id'] == prod.id:
                if item['cantidad'] + cant > prod.stock_actual: return print("Stock insuficiente")
                item['cantidad'] += cant
                item['precio_unitario'] = precio_custom 
                item['subtotal'] = item['cantidad'] * precio_custom
                encontrado = True
                break
        
        if not encontrado:
            self.carrito.append({
                'producto_id': prod.id,
                'nombre': f"{prod.nombre} ({prod.color or 'N/A'})",
                'cantidad': cant,
                'precio_unitario': precio_custom,
                'subtotal': cant * precio_custom
            })

        self.actualizar_tabla_carrito()
        self.entry_cant.delete(0, 'end')
        self.entry_cant.insert(0, "1")
        self.al_seleccionar_producto(self.combo_prod.get())

    def quitar_del_carrito(self):
        seleccion = self.tree_carrito.selection()
        if not seleccion: return
        id_prod = int(self.tree_carrito.item(seleccion[0])['values'][0])
        self.carrito = [item for item in self.carrito if item['producto_id'] != id_prod]
        self.actualizar_tabla_carrito()

    def actualizar_tabla_carrito(self):
        for item in self.tree_carrito.get_children(): self.tree_carrito.delete(item)
        for item in self.carrito:
            self.tree_carrito.insert("", "end", values=(
                item['producto_id'], item['nombre'], item['cantidad'], 
                f"$ {item['precio_unitario']:,.0f}", f"$ {item['subtotal']:,.0f}"
            ))
        self.actualizar_totales()

    def actualizar_totales(self, event=None):
        subtotal_prod = sum(item['subtotal'] for item in self.carrito)
        total = subtotal_prod
        self.lbl_subtotal.configure(text=f"Subtotal Prod: $ {subtotal_prod:,.0f}")
        self.lbl_total_cobrar.configure(text=f"TOTAL A COBRAR: $ {total:,.0f}")

    def confirmar_venta(self):
        if not self.carrito: return
        cliente = self.entry_cliente.get() or "Cliente Mostrador"
        tipo_dom = self.combo_domicilio.get()
        estado_pago = "Pagado" if self.combo_estado_pago.get() == "Pagado Completo" else "Abono"
        abono = 0.0
        
        if estado_pago == "Abono":
            try: abono = float(self.entry_abono.get() or 0)
            except: return print("Monto de abono inválido")

        try: valor_dom_negocio = float(self.entry_valor_domicilio.get() or 0)
        except: return print("Valor domicilio inválido")

        cobro_cliente = 0 
        pago_trans = valor_dom_negocio if "Envío gratis" in tipo_dom else 0 

        detalles = [{'producto_id': item['producto_id'], 'cantidad': item['cantidad'], 'precio_unitario': item['precio_unitario']} for item in self.carrito]
        
        exito, msg = controllers.registrar_venta(
            cliente, detalles, 0, tipo_dom, cobro_cliente, pago_trans, 
            self.combo_pago.get(), estado_pago, abono
        )

        if exito:
            self.carrito = []
            self.actualizar_tabla_carrito()
            self.cargar_productos_disponibles()
            self.entry_cliente.delete(0, 'end')
            
            self.combo_estado_pago.set("Pagado Completo")
            self.frame_abono.pack_forget()
            self.combo_domicilio.set("1. Cliente recoge")
            self.frame_valores_dom.pack_forget()
            self.entry_abono.delete(0, 'end')
            self.entry_abono.insert(0, "0")
            self.entry_valor_domicilio.delete(0, 'end')
            self.entry_valor_domicilio.insert(0, "0")
            
            print("Venta registrada con éxito")
        else:
            print(f"Error: {msg}")