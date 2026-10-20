import customtkinter as ctk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Compra, Proveedor
import controllers

class VistaHistorialCompras(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(self, text="Historial de Compras de Mercancía", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # Tabla
        self.aplicar_estilo_tabla()
        self.tree = ttk.Treeview(self, columns=("id", "fecha", "proveedor", "total", "metodo"), show="headings", height=20)
        self.tree.heading("id", text="N° Compra")
        self.tree.heading("fecha", text="Fecha de Compra")
        self.tree.heading("proveedor", text="Proveedor")
        self.tree.heading("total", text="Total Pagado")
        self.tree.heading("metodo", text="Método de Pago")
        
        self.tree.column("id", width=80, anchor="center")
        self.tree.column("fecha", width=150, anchor="center")
        self.tree.column("proveedor", width=200)
        self.tree.column("total", width=120, anchor="e")
        self.tree.column("metodo", width=120, anchor="center")
        
        self.tree.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="🗑️ Revertir / Eliminar Compra Seleccionada", fg_color="#dc3545", hover_color="#c82333", font=ctk.CTkFont(weight="bold"), command=self.eliminar_compra).pack(pady=15)

        self.cargar_compras()

    def aplicar_estilo_tabla(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', '#1f538d')])

    def cargar_compras(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        with SessionLocal() as db:
            compras = db.query(Compra).order_by(Compra.id.desc()).all()
            for c in compras:
                prov_nombre = c.proveedor.nombre if c.proveedor else "Proveedor Eliminado"
                self.tree.insert("", "end", values=(c.id, c.fecha.strftime("%Y-%m-%d %H:%M"), prov_nombre, f"$ {c.total:,.0f}", c.metodo_pago))

    def eliminar_compra(self):
        seleccion = self.tree.selection()
        if not seleccion:
            return messagebox.showwarning("Atención", "Selecciona una compra de la tabla primero.")
            
        id_compra = int(self.tree.item(seleccion[0])['values'][0])
        
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación", 
            "¿Estás seguro de revertir esta compra?\n\n- Se descontarán los productos del inventario.\n- El dinero invertido regresará a tus Finanzas."
        )
        
        if confirmacion:
            exito, msg = controllers.revertir_compra(id_compra)
            if exito:
                self.cargar_compras()
                print(msg)
            else:
                messagebox.showerror("Error", f"No se pudo revertir: {msg}")