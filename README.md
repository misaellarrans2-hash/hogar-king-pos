# Hogar King POS

Sistema de punto de venta a la medida para **Hogar King** (papelería y hogar),
con 2 sedes en Santa Marta: **Sede Centro** y **Sede La Lucha**.

Este proyecto es una prueba de concepto (MVP) para mostrarle a la empresa una
alternativa mejor al sistema actual (Mayasis + cuaderno/Excel), enfocada en
resolver problemas reales del día a día: control de inventario, precios
correctos, y visibilidad entre las 2 sedes.

## Diferenciales frente al sistema actual

- **El bodeguero puede manejar el inventario desde su celular** (entradas,
  salidas), no solo desde el computador.
- **Consulta y solicitud de traslado de productos entre sedes** desde el
  sistema, sin depender de llamadas o WhatsApp.
- **Permisos finos por rol y por sede**: nadie de Sede Centro puede ver ni
  tocar precios, costos o inventario de Sede La Lucha (y viceversa).
- Pago único, sin mensualidades.

## Roles del sistema

| Rol | Ve | No ve | Objetivo |
|---|---|---|---|
| SUPERADMIN | Todo de las 2 sedes, costos y ganancias | Nada | El dueño, control total |
| ADMINSEDE | Todo de su sede, precios | Costos, la otra sede | Administrador de cada tienda |
| CAJERO | Vender, cobrar, cierre de su caja | Costos, inventario de la otra sede | Cobrar rápido |
| BODEGUERO | Inventario, entradas, traslados de su sede | Precios, ventas | Cuidar la mercancía |
| ASESOR | Precios y stock de su sede | Costos, ventas | Atender y cotizar clientes |

## Estado actual

**PR #1 — Esqueleto, base de datos, login y permisos**
- [x] Esqueleto del proyecto (Flask + SQLAlchemy + Bootstrap 5, sin depender de internet)
- [x] Base de datos: Sede, Rol, Usuario
- [x] Login y sesiones
- [x] Permisos por rol y por sede (decorador `roles_requeridos`, helpers en `Usuario`)
- [x] Datos de ejemplo (2 sedes, 5 roles, 9 usuarios demo) para poder mostrar el sistema
- [x] Script de respaldo simple de la base de datos

**PR #2 — Inventario**
- [x] Productos y stock por sede (un mismo producto puede existir en 1 o las 2 sedes, con cantidades distintas)
- [x] Registrar entradas y salidas, con formulario grande pensado para celular (pistola de codigo de barras o escritura manual)
- [x] Alerta visual de stock bajo
- [x] Historial de movimientos de inventario por sede
- [x] Importar productos desde Excel (crea o actualiza por codigo)
- [x] Historial de cambios de precio (auditoria: quien y cuando)
- [x] Reglas de permisos aplicadas: solo SUPERADMIN ve costos; BODEGUERO no ve precios; CAJERO no entra al inventario

**PR #3 — Facturación**
- [x] Venta rapida: agregar productos por codigo de barras, carrito en pantalla
- [x] 4 formas de pago: Efectivo, Datafono, Transferencia, Credito
- [x] Descuento porcentual sobre la venta
- [x] La venta descuenta el stock de la sede automaticamente
- [x] Recibo imprimible (formato angosto tipo tiquete 80mm, boton "Imprimir")
- [x] Anulacion de facturas: devuelve el stock y queda registrado quien y cuando la anulo
- [x] Historial de ventas por sede
- [x] Permisos: solo SUPERADMIN, ADMINSEDE y CAJERO venden; un CAJERO solo puede anular sus propias facturas

## Próximos PRs (en orden)

1. Cierre de caja y arqueo
2. Consulta y solicitud de traslado entre sedes
3. Reportes, dashboard, proveedores, clientes y el resto de funciones

> Nota sobre infraestructura: hoy el sistema corre en 1 sola PC (pensado para
> la demo). Si la empresa aprueba el proyecto, el paso de "varias cajas por
> sede + sincronización entre sedes" se diseña como una fase aparte, con
> presupuesto real para hosting/hardware.

## Cómo correrlo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python seed_demo_data.py        # crea la base de datos y los usuarios demo
python run.py
```

Abrir http://localhost:5000 en el navegador.

### Usuarios de prueba

La contraseña de cada usuario demo es igual a su nombre de usuario.

| Usuario | Rol | Sede |
|---|---|---|
| superadmin | SUPERADMIN | (todas) |
| admin_centro | ADMINSEDE | Sede Centro |
| admin_lalucha | ADMINSEDE | Sede La Lucha |
| cajero_centro | CAJERO | Sede Centro |
| cajero_lalucha | CAJERO | Sede La Lucha |
| bodeguero_centro | BODEGUERO | Sede Centro |
| bodeguero_lalucha | BODEGUERO | Sede La Lucha |
| asesor_centro | ASESOR | Sede Centro |
| asesor_lalucha | ASESOR | Sede La Lucha |
