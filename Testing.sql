USE sma_acuatico;

-- Ver todos los estanques
SELECT * FROM estanques;

-- Ver las últimas 10 lecturas registradas
SELECT * FROM lecturas ORDER BY fecha_hora DESC LIMIT 10;

-- Promedio de cada parámetro por estanque (esto es justo el tipo de estadística para tu dashboard)
SELECT 
    e.nombre AS estanque,
    s.parametro,
    ROUND(AVG(l.valor), 2) AS promedio
FROM lecturas l
JOIN sensores s ON l.sensor_id = s.id
JOIN estanques e ON l.estanque_id = e.id
GROUP BY e.nombre, s.parametro
ORDER BY e.nombre, s.parametro;

-- Alertas por nivel de gravedad
SELECT nivel, COUNT(*) AS cantidad
FROM alertas
GROUP BY nivel;

SELECT count(*) FROM lecturas;

SELECT sensor_id, COUNT(*) AS lecturas_por_sensor
FROM lecturas
GROUP BY sensor_id;

SHOW GRANTS FOR 'sma_eliminador'@'%';