import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from database import SessionLocal
from models import Producto
from datetime import datetime
import os

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

class VistaCotizaciones(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.carrito = []
        self.productos_dict = {}

        ctk.CTkLabel(self, text="Generador de Cotizaciones", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        self.frame_izq = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10, border_width=1, border_color="#444444")
        self.frame_izq.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.frame_der = ctk.CTkFrame(self, width=350, fg_color="#2b2b2b", corner_radius=10, border_width=1, border_color="#444444")
        self.frame_der.pack(side="right", fill="y")

        self.construir_panel_izquierdo()
        self.construir_panel_derecho()
        self.cargar_todos_los_productos()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def construir_panel_izquierdo(self):
        frame_agregar = ctk.CTkFrame(self.frame_izq, fg_color="transparent")
        frame_agregar.pack(fill="x", pady=10, padx=10)

        # --- FILA 1: Producto ---
        ctk.CTkLabel(frame_agregar, text="Producto:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.combo_prod = ctk.CTkComboBox(frame_agregar, width=400, values=["Cargando..."], state="readonly")
        self.combo_prod.grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # --- FILA 2: Cantidad y Botón ---
        ctk.CTkLabel(frame_agregar, text="Cant:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.entry_cant = ctk.CTkEntry(frame_agregar, width=70)
        self.entry_cant.insert(0, "1")
        self.entry_cant.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        ctk.CTkButton(frame_agregar, text="➕ Agregar", command=self.agregar_al_carrito).grid(row=1, column=2, padx=20, pady=10)

        self.aplicar_estilo_tabla()
        self.tree_carrito = ttk.Treeview(self.frame_izq, columns=("id", "nombre", "cant", "precio", "sub"), show="headings", height=15)
        self.tree_carrito.heading("id", text="ID")
        self.tree_carrito.heading("nombre", text="Producto")
        self.tree_carrito.heading("cant", text="Cant.")
        self.tree_carrito.heading("precio", text="Precio Unit.")
        self.tree_carrito.heading("sub", text="Subtotal")
        self.tree_carrito.column("id", width=0, stretch=False)
        self.tree_carrito.column("cant", width=50, anchor="center")
        self.tree_carrito.pack(fill="both", expand=True, padx=10)
        
        ctk.CTkButton(self.frame_izq, text="🗑️ Quitar Seleccionado", fg_color="#dc3545", hover_color="#c82333", command=self.quitar_del_carrito).pack(pady=10, padx=10, anchor="w")

    def construir_panel_derecho(self):
        ctk.CTkLabel(self.frame_der, text="Datos del Cliente", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkLabel(self.frame_der, text="Nombre del Cliente/Empresa:").pack(anchor="w", padx=20)
        self.entry_cliente = ctk.CTkEntry(self.frame_der, width=280)
        self.entry_cliente.pack(padx=20, pady=(0, 15))
        
        ctk.CTkLabel(self.frame_der, text="Teléfono / WhatsApp:").pack(anchor="w", padx=20)
        self.entry_tel = ctk.CTkEntry(self.frame_der, width=280)
        self.entry_tel.pack(padx=20, pady=(0, 20))

        ctk.CTkFrame(self.frame_der, height=2, fg_color="#444444").pack(fill="x", padx=20, pady=10)

        self.lbl_total_cotizar = ctk.CTkLabel(self.frame_der, text="TOTAL COTIZADO: $ 0", font=ctk.CTkFont(size=20, weight="bold"), text_color="#17a2b8")
        self.lbl_total_cotizar.pack(anchor="e", padx=20, pady=20)

        ctk.CTkButton(self.frame_der, text="📄 Generar PDF Cotización", height=45, fg_color="#17a2b8", hover_color="#138496", font=ctk.CTkFont(weight="bold", size=15), command=self.generar_pdf).pack(padx=20, pady=10, fill="x")

    def cargar_todos_los_productos(self):
        with SessionLocal() as db:
            productos = db.query(Producto).all()
            self.productos_dict = {f"{p.sku} - {p.nombre} (Color: {p.color or 'N/A'}) ($ {p.precio_venta:,.0f})": p for p in productos}
            
            if self.productos_dict:
                self.combo_prod.configure(values=list(self.productos_dict.keys()))
                self.combo_prod.set(list(self.productos_dict.keys())[0])
            else:
                self.combo_prod.configure(values=["No hay productos registrados"])

    def agregar_al_carrito(self):
        seleccion = self.combo_prod.get()
        if seleccion not in self.productos_dict: return
        
        prod = self.productos_dict[seleccion]
        try:
            cant = int(self.entry_cant.get())
            if cant <= 0: raise ValueError
        except:
            return print("Cantidad inválida")

        encontrado = False
        for item in self.carrito:
            if item['producto_id'] == prod.id:
                item['cantidad'] += cant
                item['subtotal'] = item['cantidad'] * prod.precio_venta
                encontrado = True
                break
        
        if not encontrado:
            self.carrito.append({
                'producto_id': prod.id,
                'nombre': f"{prod.nombre} ({prod.color or 'N/A'})",
                'cantidad': cant,
                'precio_unitario': prod.precio_venta,
                'subtotal': cant * prod.precio_venta
            })

        self.actualizar_tabla_carrito()
        self.entry_cant.delete(0, 'end')
        self.entry_cant.insert(0, "1")

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
        total = sum(item['subtotal'] for item in self.carrito)
        self.lbl_total_cotizar.configure(text=f"TOTAL COTIZADO: $ {total:,.0f}")

    def generar_pdf(self):
        if not FPDF: return print("Instala la librería fpdf primero")
        if not self.carrito: return print("El carrito de cotización está vacío")
            
        cliente = self.entry_cliente.get() or "Cliente Mostrador"
        telefono = self.entry_tel.get() or "N/A"
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        nombre_sugerido = f"Cotizacion_{cliente.replace(' ', '_')}_{fecha_actual}.pdf"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".pdf", 
            initialfile=nombre_sugerido,
            title="Guardar Cotización",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        
        if not filepath: return
        total = sum(item['subtotal'] for item in self.carrito)
        
        pdf = FPDF()
        pdf.add_page()
        
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            pdf.image(logo_path, x=85, y=10, w=40)
            pdf.set_y(55) 
        else:
            pdf.set_y(20) 
        
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(190, 10, txt="COTIZACIÓN DE PRODUCTOS Y SERVICIOS", ln=True, align='C')
        pdf.set_font("Arial", '', 12)
        pdf.cell(190, 10, txt=f"Fecha de emisión: {fecha_actual}", ln=True, align='C')
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, txt=f"Cliente / Empresa: {cliente}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(190, 8, txt=f"Teléfono: {telefono}", ln=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 11)
        pdf.set_fill_color(200, 200, 200)
        pdf.cell(90, 10, "Descripción del Producto", 1, 0, 'C', fill=True)
        pdf.cell(20, 10, "Cant.", 1, 0, 'C', fill=True)
        pdf.cell(40, 10, "V. Unitario", 1, 0, 'C', fill=True)
        pdf.cell(40, 10, "Subtotal", 1, 1, 'C', fill=True)
        
        pdf.set_font("Arial", '', 11)
        for item in self.carrito:
            nombre_corto = item['nombre'][:40] + "..." if len(item['nombre']) > 40 else item['nombre']
            pdf.cell(90, 10, nombre_corto, 1)
            pdf.cell(20, 10, str(item['cantidad']), 1, 0, 'C')
            pdf.cell(40, 10, f"$ {item['precio_unitario']:,.0f}", 1, 0, 'R')
            pdf.cell(40, 10, f"$ {item['subtotal']:,.0f}", 1, 1, 'R')
            
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(150, 10, "TOTAL A PAGAR:", 0, 0, 'R')
        pdf.cell(40, 10, f"$ {total:,.0f}", 0, 1, 'R')
        
        pdf.ln(15)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, txt="MÉTODOS DE PAGO AUTORIZADOS:", ln=True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(190, 6, txt="- Nequi: 322 625 4099 (Neoon Publitodo)", ln=True)
        pdf.cell(190, 6, txt="- Daviplata: 312 886 8412", ln=True)
        
        pdf.ln(15)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 6, txt="* Esta cotización tiene una validez de 5 días hábiles a partir de la fecha de emisión.", ln=True, align='C')
        pdf.cell(190, 6, txt="* Todo trabajo personalizado requiere un anticipo del 50% para iniciar producción.", ln=True, align='C')
        
        try:
            pdf.output(filepath)
            os.startfile(filepath)
            self.carrito = []
            self.actualizar_tabla_carrito()
            self.entry_cliente.delete(0, 'end')
            self.entry_tel.delete(0, 'end')
        except Exception as e:
            print(f"Error al generar PDF: {e}")