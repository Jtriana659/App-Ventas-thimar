from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class TipoMovimiento(enum.Enum):
    ENTRADA_COMPRA = "Entrada por Compra"
    SALIDA_VENTA = "Salida por Venta"
    AJUSTE = "Ajuste de Inventario"
    SALDO_INICIAL = "Saldo Inicial"

class Categoria(Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(50), unique=True, nullable=False)
    activa = Column(Boolean, default=True)
    productos = relationship("Producto", back_populates="categoria")

class Proveedor(Base):
    __tablename__ = 'proveedores'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(20))
    activo = Column(Boolean, default=True)
    compras = relationship("Compra", back_populates="proveedor")

class Producto(Base):
    __tablename__ = 'productos'
    id = Column(Integer, primary_key=True)
    sku = Column(String(20), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))
    
    dimensiones = Column(String(50))
    color = Column(String(50))
    
    costo_unitario = Column(Float, default=0.0)
    precio_venta = Column(Float, nullable=False)
    stock_actual = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=3)
    categoria_id = Column(Integer, ForeignKey('categorias.id'))
    proveedor_habitual = Column(String(100))
    fecha_registro = Column(DateTime, default=datetime.now)
    activo = Column(Boolean, default=True)
    
    categoria = relationship("Categoria", back_populates="productos")

class MovimientoInventario(Base):
    __tablename__ = 'movimientos_inventario'
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('productos.id'), nullable=False)
    tipo = Column(Enum(TipoMovimiento), nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.now)
    observaciones = Column(String(200))

class Compra(Base):
    __tablename__ = 'compras'
    id = Column(Integer, primary_key=True)
    proveedor_id = Column(Integer, ForeignKey('proveedores.id'))
    fecha = Column(DateTime, default=datetime.now)
    subtotal = Column(Float, default=0.0)
    costo_envio = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    estado_pago = Column(String(20))
    estado_recepcion = Column(String(20))
    metodo_pago = Column(String(50))
    
    proveedor = relationship("Proveedor", back_populates="compras")
    detalles = relationship("DetalleCompra", back_populates="compra")

class DetalleCompra(Base):
    __tablename__ = 'detalles_compra'
    id = Column(Integer, primary_key=True)
    compra_id = Column(Integer, ForeignKey('compras.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    costo_unitario_base = Column(Float, nullable=False)
    
    compra = relationship("Compra", back_populates="detalles")

class Venta(Base):
    __tablename__ = 'ventas'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    cliente = Column(String(100))
    subtotal = Column(Float, nullable=False)
    descuento = Column(Float, default=0.0)
    tipo_domicilio = Column(String(50))
    ingreso_domicilio = Column(Float, default=0.0)
    gasto_domicilio = Column(Float, default=0.0)
    total_cobrado = Column(Float, nullable=False)
    metodo_pago = Column(String(50))
    estado_pago = Column(String(20))

    # --- NUEVOS CAMPOS ---
    monto_pagado = Column(Float, default=0.0)
    saldo_pendiente = Column(Float, default=0.0)
    # ---------------------
    
    metodo_pago = Column(String(50))
    estado_pago = Column(String(20))
    
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = 'detalles_venta'
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey('ventas.id'))
    producto_id = Column(Integer, ForeignKey('productos.id'))
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    costo_unitario_historico = Column(Float, nullable=False)
    
    venta = relationship("Venta", back_populates="detalles")

class TransaccionFinanciera(Base):
    __tablename__ = 'transacciones_financieras'
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.now)
    tipo = Column(String(50))
    categoria = Column(String(50))
    monto = Column(Float, nullable=False)
    referencia_id = Column(Integer)
    observaciones = Column(String(255))