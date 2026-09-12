-- ============================================================
-- Sistema de Monitoreo Acuícola (SMA) - Acuática del Golfo S.A.
-- Esquema + datos de ejemplo
-- ============================================================

CREATE DATABASE IF NOT EXISTS sma_acuatico
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sma_acuatico;

-- Estanques de cultivo
CREATE TABLE estanques (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(50) NOT NULL,
  tipo_cultivo ENUM('tilapia','camaron') NOT NULL,
  capacidad_m3 DECIMAL(8,2) NOT NULL,
  fecha_alta DATE NOT NULL
);

-- Sensores instalados por estanque (módulo MAD)
CREATE TABLE sensores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  estanque_id INT NOT NULL,
  parametro ENUM('temperatura','ph','oxigeno_disuelto','salinidad') NOT NULL,
  modelo VARCHAR(50) NOT NULL,
  fecha_instalacion DATE NOT NULL,
  FOREIGN KEY (estanque_id) REFERENCES estanques(id)
);

-- Lecturas históricas (alimentan el patrón Observer en la UI)
CREATE TABLE lecturas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  sensor_id INT NOT NULL,
  estanque_id INT NOT NULL,
  valor DECIMAL(6,2) NOT NULL,
  fecha_hora DATETIME NOT NULL,
  FOREIGN KEY (sensor_id) REFERENCES sensores(id),
  FOREIGN KEY (estanque_id) REFERENCES estanques(id),
  INDEX idx_estanque_fecha (estanque_id, fecha_hora)
);

-- Alertas generadas por el módulo de procesamiento (patrón Strategy)
CREATE TABLE alertas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  estanque_id INT NOT NULL,
  parametro ENUM('temperatura','ph','oxigeno_disuelto','salinidad') NOT NULL,
  valor_detectado DECIMAL(6,2) NOT NULL,
  nivel ENUM('bajo','medio','critico') NOT NULL,
  mensaje VARCHAR(150) NOT NULL,
  fecha_hora DATETIME NOT NULL,
  atendida BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (estanque_id) REFERENCES estanques(id)
);

-- Usuarios de la aplicación (distintos de los usuarios de MySQL del otro script)
CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  rol ENUM('operario','supervisor','administrador') NOT NULL,
  fecha_alta DATE NOT NULL
);

-- ============================================================
-- DATOS DE EJEMPLO
-- ============================================================

INSERT INTO estanques (nombre, tipo_cultivo, capacidad_m3, fecha_alta) VALUES
('Estanque A1', 'tilapia', 500.00, '2024-01-15'),
('Estanque A2', 'tilapia', 500.00, '2024-01-15'),
('Estanque B1', 'camaron', 800.00, '2024-03-10'),
('Estanque B2', 'camaron', 800.00, '2024-03-10');

INSERT INTO sensores (estanque_id, parametro, modelo, fecha_instalacion) VALUES
(1,'temperatura','TS-100','2024-01-20'),(1,'ph','PH-200','2024-01-20'),
(1,'oxigeno_disuelto','OD-300','2024-01-20'),(1,'salinidad','SA-400','2024-01-20'),
(2,'temperatura','TS-100','2024-01-20'),(2,'ph','PH-200','2024-01-20'),
(2,'oxigeno_disuelto','OD-300','2024-01-20'),(2,'salinidad','SA-400','2024-01-20'),
(3,'temperatura','TS-100','2024-03-15'),(3,'ph','PH-200','2024-03-15'),
(3,'oxigeno_disuelto','OD-300','2024-03-15'),(3,'salinidad','SA-400','2024-03-15'),
(4,'temperatura','TS-100','2024-03-15'),(4,'ph','PH-200','2024-03-15'),
(4,'oxigeno_disuelto','OD-300','2024-03-15'),(4,'salinidad','SA-400','2024-03-15');

INSERT INTO usuarios (nombre, email, rol, fecha_alta) VALUES
('Juan Pérez','juan.perez@acuaticadelgolfo.mx','operario','2024-01-10'),
('María López','maria.lopez@acuaticadelgolfo.mx','operario','2024-01-10'),
('Carlos Ruiz','carlos.ruiz@acuaticadelgolfo.mx','supervisor','2024-01-05'),
('Ana Torres','ana.torres@acuaticadelgolfo.mx','administrador','2023-12-01');

-- Generador de lecturas: 3 días, cada 4 horas -> 18 lecturas por sensor
-- 16 sensores x 18 = 288 filas en total (suficiente para graficar, no exagerado)
DELIMITER //
CREATE PROCEDURE generar_lecturas()
BEGIN
  DECLARE i INT DEFAULT 0;
  DECLARE fecha_base DATETIME DEFAULT DATE_SUB(NOW(), INTERVAL 3 DAY);
  DECLARE s_id INT;
  DECLARE e_id INT;
  DECLARE param VARCHAR(20);
  DECLARE done INT DEFAULT FALSE;

  DECLARE cur CURSOR FOR SELECT id, estanque_id, parametro FROM sensores;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO s_id, e_id, param;
    IF done THEN
      LEAVE read_loop;
    END IF;

    SET i = 0;
    WHILE i < 18 DO
      INSERT INTO lecturas (sensor_id, estanque_id, valor, fecha_hora)
      VALUES (
        s_id, e_id,
        CASE param
          WHEN 'temperatura' THEN ROUND(26 + RAND()*6, 2)      -- 26-32 °C
          WHEN 'ph' THEN ROUND(6.5 + RAND()*1.5, 2)             -- 6.5-8.0
          WHEN 'oxigeno_disuelto' THEN ROUND(3 + RAND()*5, 2)   -- 3-8 mg/L
          WHEN 'salinidad' THEN ROUND(RAND()*20, 2)             -- 0-20 ppt
        END,
        DATE_ADD(fecha_base, INTERVAL i*4 HOUR)
      );
      SET i = i + 1;
    END WHILE;
  END LOOP;
  CLOSE cur;
END //
DELIMITER ;

CALL generar_lecturas();
DROP PROCEDURE generar_lecturas;

-- Alertas de ejemplo (para poder mostrar estadísticas de alertas por nivel/estanque)
INSERT INTO alertas (estanque_id, parametro, valor_detectado, nivel, mensaje, fecha_hora, atendida) VALUES
(1,'oxigeno_disuelto',2.10,'critico','Oxígeno disuelto por debajo del mínimo seguro', DATE_SUB(NOW(), INTERVAL 2 DAY), TRUE),
(2,'ph',8.60,'medio','pH elevado, revisar aireación', DATE_SUB(NOW(), INTERVAL 1 DAY), FALSE),
(3,'temperatura',33.20,'medio','Temperatura por encima del rango óptimo', DATE_SUB(NOW(), INTERVAL 18 HOUR), FALSE),
(4,'salinidad',22.50,'bajo','Salinidad ligeramente elevada', DATE_SUB(NOW(), INTERVAL 10 HOUR), TRUE),
(1,'oxigeno_disuelto',2.80,'medio','Oxígeno disuelto bajo, monitorear', DATE_SUB(NOW(), INTERVAL 5 HOUR), FALSE);