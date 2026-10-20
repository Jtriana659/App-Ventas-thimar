import sqlite3

# Nos conectamos a tu base de datos actual
conexion = sqlite3.connect("negocio_data.db")
cursor = conexion.cursor()

try:
    # Agregamos la columna dimensiones
    cursor.execute("ALTER TABLE productos ADD COLUMN dimensiones VARCHAR(50)")
    print("✅ Columna 'dimensiones' agregada correctamente.")
except Exception as e:
    print("Aviso dimensiones:", e)

try:
    # Agregamos la columna color
    cursor.execute("ALTER TABLE productos ADD COLUMN color VARCHAR(50)")
    print("✅ Columna 'color' agregada correctamente.")
except Exception as e:
    print("Aviso color:", e)

conexion.commit()
conexion.close()
print("🎉 ¡Base de datos actualizada con éxito! Ya puedes usar la app.")