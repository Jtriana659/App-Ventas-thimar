from datetime import datetime
from database import SessionLocal
from models import Producto, Venta, DetalleVenta, TransaccionFinanciera, MovimientoInventario, TipoMovimiento, Compra, DetalleCompra

def registrar_capital_inicial(monto: float = 500000.0):
    with SessionLocal() as db:
        existe = db.query(TransaccionFinanciera).filter_by(categoria="Capital Inicial").first()
        if not existe:
            db.add(TransaccionFinanciera(tipo="Ingreso", categoria="Capital Inicial", monto=monto, observaciones="Aporte inicial"))
            db.commit()

def registrar_venta(cliente, detalles, descuento, tipo_domicilio, cobro_domicilio_cliente, pago_transportador, metodo_pago, estado_pago, abono_inicial):
    with SessionLocal() as db:
        try:
            # AHORA EL SUBTOTAL SE CALCULA CON EL PRECIO PERSONALIZADO QUE ENVÍAS DESDE LA INTERFAZ
            subtotal = sum(d['cantidad'] * d['precio_unitario'] for d in detalles)
            
            ingreso_dom = cobro_domicilio_cliente if tipo_domicilio == "Paga cliente" else 0
            gasto_dom = pago_transportador
            total = subtotal - descuento + ingreso_dom
            
            if estado_pago == "Pagado":
                monto_pagado = total
                saldo_pendiente = 0
            else: # Abono
                monto_pagado = abono_inicial
                saldo_pendiente = total - abono_inicial

            venta = Venta(
                cliente=cliente, subtotal=subtotal, descuento=descuento, tipo_domicilio=tipo_domicilio,
                ingreso_domicilio=ingreso_dom, gasto_domicilio=gasto_dom, total_cobrado=total,
                monto_pagado=monto_pagado, saldo_pendiente=saldo_pendiente,
                metodo_pago=metodo_pago, estado_pago=estado_pago
            )
            db.add(venta)
            db.flush()

            for d in detalles:
                prod = db.query(Producto).get(d['producto_id'])
                prod.stock_actual -= d['cantidad']
                db.add(MovimientoInventario(producto_id=prod.id, tipo=TipoMovimiento.SALIDA_VENTA, cantidad=-d['cantidad'], observaciones=f"Venta #{venta.id}"))
                # SE GUARDA EL PRECIO UNITARIO PERSONALIZADO EN EL DETALLE DE LA VENTA
                db.add(DetalleVenta(venta_id=venta.id, producto_id=prod.id, cantidad=d['cantidad'], precio_unitario=d['precio_unitario'], costo_unitario_historico=prod.costo_unitario))

            if monto_pagado > 0:
                db.add(TransaccionFinanciera(tipo="Ingreso", categoria="Venta", monto=monto_pagado, referencia_id=venta.id, observaciones=f"Ingreso Venta #{venta.id}"))
            
            if gasto_dom > 0:
                db.add(TransaccionFinanciera(tipo="Egreso", categoria="Gasto Domicilio", monto=gasto_dom, referencia_id=venta.id))

            db.commit()
            return True, "Venta registrada"
        except Exception as e:
            db.rollback()
            return False, str(e)

def pagar_saldo_pendiente(id_venta, monto_abono, metodo_pago):
    with SessionLocal() as db:
        try:
            venta = db.query(Venta).get(id_venta)
            if not venta: return False, "Venta no encontrada"
            if monto_abono > venta.saldo_pendiente:
                return False, "El abono supera la deuda"

            venta.monto_pagado += monto_abono
            venta.saldo_pendiente -= monto_abono
            
            if venta.saldo_pendiente <= 0:
                venta.estado_pago = "Pagado"
            
            db.add(TransaccionFinanciera(tipo="Ingreso", categoria="Pago CxC", monto=monto_abono, referencia_id=venta.id, observaciones=f"Abono a Venta #{venta.id}"))
            db.commit()
            return True, "Abono registrado"
        except Exception as e:
            db.rollback()
            return False, str(e)

def registrar_gasto_operativo(categoria, monto, observaciones):
    with SessionLocal() as db:
        try:
            gasto = TransaccionFinanciera(tipo="Egreso", categoria=categoria, monto=monto, referencia_id=0, observaciones=observaciones)
            db.add(gasto)
            db.commit()
            return True, "Gasto registrado con éxito"
        except Exception as e:
            db.rollback()
            return False, str(e)

def registrar_baja_inventario(producto_id, cantidad, motivo):
    with SessionLocal() as db:
        try:
            prod = db.query(Producto).get(producto_id)
            if not prod or prod.stock_actual < cantidad:
                return False, "Stock insuficiente para dar de baja."
            
            prod.stock_actual -= cantidad
            mov = MovimientoInventario(producto_id=prod.id, tipo=TipoMovimiento.AJUSTE, cantidad=-cantidad, observaciones=motivo)
            db.add(mov)

            perdida = prod.costo_unitario * cantidad
            if perdida > 0:
                tx = TransaccionFinanciera(tipo="Egreso", categoria="Pérdida por Daño/Merma", monto=perdida, referencia_id=prod.id, observaciones=f"Baja de {cantidad}x {prod.nombre} ({motivo})")
                db.add(tx)

            db.commit()
            return True, "Baja de inventario registrada."
        except Exception as e:
            db.rollback()
            return False, str(e)

def eliminar_registro_gasto_dano(tipo_db, id_db):
    with SessionLocal() as db:
        try:
            if tipo_db == "GASTO":
                gasto = db.query(TransaccionFinanciera).get(id_db)
                if gasto:
                    db.delete(gasto)
            elif tipo_db == "DANO":
                mov = db.query(MovimientoInventario).get(id_db)
                if mov:
                    prod = db.query(Producto).get(mov.producto_id)
                    if prod:
                        prod.stock_actual += abs(mov.cantidad)
                        obs_esperada = f"Baja de {abs(mov.cantidad)}x {prod.nombre} ({mov.observaciones})"
                        tx = db.query(TransaccionFinanciera).filter(
                            TransaccionFinanciera.categoria == "Pérdida por Daño/Merma", TransaccionFinanciera.referencia_id == prod.id, TransaccionFinanciera.observaciones == obs_esperada
                        ).first()
                        if tx: db.delete(tx)
                    db.delete(mov)
            db.commit()
            return True, "Registro eliminado y valores restaurados correctamente."
        except Exception as e:
            db.rollback()
            return False, str(e)

def revertir_compra(id_compra):
    with SessionLocal() as db:
        try:
            compra = db.query(Compra).get(id_compra)
            if not compra: return False, "Compra no encontrada"
            
            detalles = db.query(DetalleCompra).filter(DetalleCompra.compra_id == compra.id).all()
            for d in detalles:
                prod = db.query(Producto).get(d.producto_id)
                if prod:
                    prod.stock_actual -= d.cantidad
                    if prod.stock_actual < 0: prod.stock_actual = 0
                
                movs = db.query(MovimientoInventario).filter(MovimientoInventario.producto_id == d.producto_id, MovimientoInventario.tipo == TipoMovimiento.ENTRADA_COMPRA).all()
                for m in movs:
                    if abs((m.fecha - compra.fecha).total_seconds()) < 5: db.delete(m)
                db.delete(d)
            
            txs = db.query(TransaccionFinanciera).filter(TransaccionFinanciera.tipo == "Egreso").all()
            for tx in txs:
                if abs((tx.fecha - compra.fecha).total_seconds()) < 5: db.delete(tx)
            
            db.delete(compra)
            db.commit()
            return True, "Compra eliminada. Inventario descontado y dinero devuelto a caja."
        except Exception as e:
            db.rollback()
            return False, str(e)