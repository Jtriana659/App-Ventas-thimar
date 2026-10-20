from database import SessionLocal
from models import Venta, DetalleVenta, Compra, DetalleCompra, MovimientoInventario, TransaccionFinanciera, Producto

def limpiar_datos_de_prueba():
    with SessionLocal() as db:
        try:
            # 1. Borramos los detalles (hijos)
            db.query(DetalleVenta).delete()
            db.query(DetalleCompra).delete()
            
            # 2. Borramos las transacciones principales (padres)
            db.query(Venta).delete()
            db.query(Compra).delete()
            db.query(MovimientoInventario).delete()
            
            # Borramos las finanzas (el capital inicial de $500.000 se volverá a crear solo al abrir la app)
            db.query(TransaccionFinanciera).delete()
            
            # 3. Reiniciamos el stock de todos los productos a 0 para que quede limpio
            productos = db.query(Producto).all()
            for p in productos:
                p.stock_actual = 0
            
            db.commit()
            print("✅ Ventas, Compras y Movimientos de Inventario eliminados.")
            print("✅ El stock de todos los productos se reinició a 0.")
            print("✅ Tu capital inicial de $500.000 se restaurará automáticamente al abrir la app.")
            print("🎉 ¡Sistema limpio y listo para trabajar en serio!")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    limpiar_datos_de_prueba()