import customtkinter as ctk
from database import engine
from models import Base
import controllers

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppNegocio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestión - Personalizados")
        self.geometry("1200x750")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- PANEL LATERAL (MENU) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="THIMAR", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 0))
        
        self.sub_logo = ctk.CTkLabel(self.sidebar_frame, text="Personalizados", font=ctk.CTkFont(size=12), text_color="#a8a8a8")
        self.sub_logo.grid(row=1, column=0, padx=20, pady=(0, 20))

        # --- ESTRUCTURA DE GRUPOS ---
        menu_grupos = {
            "📊 PRINCIPAL": ["Dashboard"],
            "📦 INVENTARIO": ["Categorías", "Proveedores", "Productos", "Inventario"],
            "🛒 COMERCIAL": ["Cotizaciones", "Ventas", "CxC", "Historial"],
            "💰 FINANZAS": ["Compras", "Hist. Compras", "Gastos", "Finanzas"]
        }

        fila = 2
        for grupo, menus in menu_grupos.items():
            lbl_grupo = ctk.CTkLabel(self.sidebar_frame, text=grupo, font=ctk.CTkFont(size=11, weight="bold"), text_color="#a8a8a8")
            lbl_grupo.grid(row=fila, column=0, padx=20, pady=(15, 2), sticky="w")
            fila += 1
            
            for menu in menus:
                btn = ctk.CTkButton(
                    self.sidebar_frame, 
                    text=f"  {menu}", 
                    fg_color="transparent",
                    text_color="white", 
                    hover_color="#1f538d",
                    anchor="w",
                    command=lambda m=menu: self.cambiar_vista(m)
                )
                btn.grid(row=fila, column=0, padx=15, pady=2, sticky="ew")
                fila += 1

        self.sidebar_frame.grid_rowconfigure(fila, weight=1) 

        # --- PANEL CENTRAL (VISTAS) ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.cambiar_vista("Dashboard")

    def cambiar_vista(self, nombre_vista):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        if nombre_vista == "Dashboard":
            from views.view_dashboard import VistaDashboard
            self.vista_actual = VistaDashboard(self.main_frame)
        elif nombre_vista == "Categorías":
            from views.view_categorias import VistaCategorias
            self.vista_actual = VistaCategorias(self.main_frame)
        elif nombre_vista == "Proveedores":
            from views.view_proveedores import VistaProveedores
            self.vista_actual = VistaProveedores(self.main_frame)
        elif nombre_vista == "Productos":
            from views.view_productos import VistaProductos
            self.vista_actual = VistaProductos(self.main_frame)
        elif nombre_vista == "Inventario":
            from views.view_inventario import VistaInventario
            self.vista_actual = VistaInventario(self.main_frame)
        elif nombre_vista == "Cotizaciones":
            from views.view_cotizaciones import VistaCotizaciones
            self.vista_actual = VistaCotizaciones(self.main_frame)
        elif nombre_vista == "Ventas":
            from views.view_ventas import VistaVentas
            self.vista_actual = VistaVentas(self.main_frame)
        elif nombre_vista == "CxC":
            from views.view_cxc import VistaCxC
            self.vista_actual = VistaCxC(self.main_frame)
        elif nombre_vista == "Historial":
            from views.view_historial import VistaHistorial
            self.vista_actual = VistaHistorial(self.main_frame)
        elif nombre_vista == "Compras":
            from views.view_compras import VistaCompras
            self.vista_actual = VistaCompras(self.main_frame)
        elif nombre_vista == "Hist. Compras":
            from views.view_historial_compras import VistaHistorialCompras
            self.vista_actual = VistaHistorialCompras(self.main_frame)
        elif nombre_vista == "Gastos":
            from views.view_gastos import VistaGastos
            self.vista_actual = VistaGastos(self.main_frame)
        elif nombre_vista == "Finanzas":
            from views.view_finanzas import VistaFinanzas
            self.vista_actual = VistaFinanzas(self.main_frame)
        else:
            lbl = ctk.CTkLabel(self.main_frame, text=f"Módulo: {nombre_vista}\n(En construcción)", font=ctk.CTkFont(size=24))
            lbl.pack(pady=150)

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    controllers.registrar_capital_inicial(500000)
    
    app = AppNegocio()
    app.mainloop()