import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Venta
import controllers

class VistaCxC(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self, text="Cuentas por Cobrar (Pendientes)", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # Formulario Superior
        frame_form = ctk.CTkFrame(self, corner_radius=10)
        frame_form.pack(fill="x", pady=(0, 20), ipady=10)

        ctk.CTkLabel(frame_form, text="Abonar a Venta N°:").grid(row=0, column=0, padx=15, pady=15)
        self.lbl_venta_id = ctk.CTkLabel(frame_form, text="-", font=ctk.CTkFont(weight="bold"))
        self.lbl_venta_id.grid(row=0, column=1, padx=15, pady=15)
        self.id_seleccionado = None

        ctk.CTkLabel(frame_form, text="Monto a Pagar ($):").grid(row=0, column=2, padx=15, pady=15)
        self.entry_pago = ctk.CTkEntry(frame_form, width=150)
        self.entry_pago.grid(row=0, column=3, padx=15, pady=15)

        ctk.CTkButton(frame_form, text="✅ Registrar Pago", fg_color="#28a745", hover_color="#218838", command=self.registrar_pago).grid(row=0, column=4, padx=20)

        # Tabla
        self.aplicar_estilo_tabla()
        self.tree = ttk.Treeview(self, columns=("id", "fecha", "cliente", "total", "pagado", "saldo"), show="headings", height=15)
        self.tree.heading("id", text="N° Venta")
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("cliente", text="Cliente")
        self.tree.heading("total", text="Total")
        self.tree.heading("pagado", text="Pagado")
        self.tree.heading("saldo", text="SALDO DEUDA")
        
        self.tree.column("id", width=80, anchor="center")
        self.tree.column("saldo", anchor="e")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.seleccionar_venta)
        self.cargar_deudas()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#dc3545", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def cargar_deudas(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        with SessionLocal() as db:
            ventas_pendientes = db.query(Venta).filter(Venta.saldo_pendiente > 0).all()
            for v in ventas_pendientes:
                self.tree.insert("", "end", values=(
                    v.id, v.fecha.strftime("%Y-%m-%d"), v.cliente,
                    f"$ {v.total_cobrado:,.0f}", f"$ {v.monto_pagado:,.0f}", f"$ {v.saldo_pendiente:,.0f}"
                ))

    def seleccionar_venta(self, event):
        seleccion = self.tree.selection()
        if not seleccion: return
        item = self.tree.item(seleccion[0])
        self.id_seleccionado = item['values'][0]
        self.lbl_venta_id.configure(text=str(self.id_seleccionado))
        
        saldo_limpio = str(item['values'][5]).replace("$ ", "").replace(",", "")
        self.entry_pago.delete(0, 'end')
        self.entry_pago.insert(0, saldo_limpio)

    def registrar_pago(self):
        if not self.id_seleccionado: return
        try: monto = float(self.entry_pago.get())
        except: return
        
        exito, msg = controllers.pagar_saldo_pendiente(self.id_seleccionado, monto, "Efectivo")
        if exito:
            self.lbl_venta_id.configure(text="-")
            self.entry_pago.delete(0, 'end')
            self.id_seleccionado = None
            self.cargar_deudas()
            print("Pago registrado")
        else:
            print("Error:", msg)