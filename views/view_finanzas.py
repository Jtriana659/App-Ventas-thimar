import customtkinter as ctk
from database import SessionLocal
from models import TransaccionFinanciera

class VistaFinanzas(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(self, text="Resumen Financiero (Flujo de Caja)", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20), anchor="w")

        # Tarjetas de resumen
        self.frame_tarjetas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tarjetas.pack(fill="x", pady=10)

        self.lbl_capital = self.crear_tarjeta(self.frame_tarjetas, "Capital Inicial", "$ 0", 0)
        self.lbl_ingresos = self.crear_tarjeta(self.frame_tarjetas, "Ingresos (Ventas)", "$ 0", 1, color="#28a745")
        self.lbl_egresos = self.crear_tarjeta(self.frame_tarjetas, "Egresos (Compras/Gastos)", "$ 0", 2, color="#dc3545")
        
        # Tarjeta principal: Dinero Actual
        self.frame_total = ctk.CTkFrame(self, corner_radius=15, border_width=2, border_color="#1f538d")
        self.frame_total.pack(fill="x", pady=20, ipady=20)
        ctk.CTkLabel(self.frame_total, text="DINERO REAL DISPONIBLE EN CAJA", font=ctk.CTkFont(size=16)).pack()
        self.lbl_caja_real = ctk.CTkLabel(self.frame_total, text="$ 0", font=ctk.CTkFont(size=40, weight="bold"), text_color="#1f538d")
        self.lbl_caja_real.pack()

        ctk.CTkButton(self, text="🔄 Actualizar Finanzas", command=self.calcular_finanzas).pack(pady=20)
        
        self.calcular_finanzas()

    def crear_tarjeta(self, master, titulo, valor, col, color="white"):
        frame = ctk.CTkFrame(master, corner_radius=10)
        frame.grid(row=0, column=col, padx=10, sticky="nsew")
        master.grid_columnconfigure(col, weight=1)
        
        ctk.CTkLabel(frame, text=titulo, font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        lbl_valor = ctk.CTkLabel(frame, text=valor, font=ctk.CTkFont(size=22, weight="bold"), text_color=color)
        lbl_valor.pack(pady=(0, 15))
        return lbl_valor

    def calcular_finanzas(self):
        with SessionLocal() as db:
            transacciones = db.query(TransaccionFinanciera).all()
            
            capital_inicial = 0
            ingresos = 0
            egresos = 0
            
            for t in transacciones:
                if t.categoria == "Capital Inicial":
                    capital_inicial += t.monto
                elif t.tipo == "Ingreso":
                    ingresos += t.monto
                elif t.tipo == "Egreso":
                    egresos += t.monto
                    
            dinero_actual = capital_inicial + ingresos - egresos
            
            self.lbl_capital.configure(text=f"$ {capital_inicial:,.0f}")
            self.lbl_ingresos.configure(text=f"$ {ingresos:,.0f}")
            self.lbl_egresos.configure(text=f"$ {egresos:,.0f}")
            
            # Si el dinero actual es negativo, se pone rojo
            color_caja = "#1f538d" if dinero_actual >= 0 else "#dc3545"
            self.lbl_caja_real.configure(text=f"$ {dinero_actual:,.0f}", text_color=color_caja)