import sqlite3

conexion = sqlite3.connect("negocio_data.db")
cursor = conexion.cursor()

try:
    cursor.execute("ALTER TABLE ventas ADD COLUMN monto_pagado FLOAT DEFAULT 0")
    print("✅ Columna 'monto_pagado' agregada.")
except Exception as e:
    print("Aviso monto_pagado:", e)

try:
    cursor.execute("ALTER TABLE ventas ADD COLUMN saldo_pendiente FLOAT DEFAULT 0")
    print("✅ Columna 'saldo_pendiente' agregada.")
except Exception as e:
    print("Aviso saldo_pendiente:", e)

# Actualizamos las ventas antiguas para que figuren como "totalmente pagadas" y no alteren las cuentas
cursor.execute("UPDATE ventas SET monto_pagado = total_cobrado, saldo_pendiente = 0 WHERE monto_pagado IS NULL")

conexion.commit()
conexion.close()
print("🎉 Base de datos lista para manejar Abonos y Cuentas por Cobrar.")