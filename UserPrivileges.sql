-- ============================================================
-- Privilegios de acceso a sma_acuatico
-- Ejecutar como root o usuario con permiso GRANT
-- Cambia las contraseñas antes de usar en producción
-- ============================================================

-- Solo LECTURA (dashboards, reportes)
CREATE USER IF NOT EXISTS 'sma_lector'@'%' IDENTIFIED BY 'Lectura#2026';
GRANT SELECT ON sma_acuatico.* TO 'sma_lector'@'%';

-- ESCRITURA (ej. módulo MAD insertando lecturas de sensores)
CREATE USER IF NOT EXISTS 'sma_escritor'@'%' IDENTIFIED BY 'Escritura#2026';
GRANT SELECT, INSERT ON sma_acuatico.* TO 'sma_escritor'@'%';

-- EDICIÓN (ej. marcar alertas como atendidas, corregir registros)
CREATE USER IF NOT EXISTS 'sma_editor'@'%' IDENTIFIED BY 'Edicion#2026';
GRANT SELECT, UPDATE ON sma_acuatico.* TO 'sma_editor'@'%';

-- ELIMINACIÓN (ej. depurar históricos antiguos)
CREATE USER IF NOT EXISTS 'sma_eliminador'@'%' IDENTIFIED BY 'Eliminacion#2026';
GRANT SELECT, DELETE ON sma_acuatico.* TO 'sma_eliminador'@'%';

-- ADMINISTRADOR (control total)
CREATE USER IF NOT EXISTS 'sma_admin'@'%' IDENTIFIED BY 'Admin#2026';
GRANT ALL PRIVILEGES ON sma_acuatico.* TO 'sma_admin'@'%';

FLUSH PRIVILEGES;

-- Para revisar los privilegios de un usuario:
-- SHOW GRANTS FOR 'sma_lector'@'%';