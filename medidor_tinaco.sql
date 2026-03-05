-- ═══════════════════════════════════════════════════════════════
--  medidor_tinaco.sql
--  Medidor Inteligente de Niveles – UTC
--  Ramos Arizpe, Coahuila · 2025
--
--  Importar en phpMyAdmin:
--    Base de datos → Importar → selecciona este archivo → Continuar
--
--  O desde terminal:
--    sudo mysql -u root -p < medidor_tinaco.sql
-- ═══════════════════════════════════════════════════════════════

-- ── 1. Crear base de datos ─────────────────────────────────────
CREATE DATABASE IF NOT EXISTS medidor_tinaco
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE medidor_tinaco;

-- ── 2. Tabla: tinacos ──────────────────────────────────────────
-- Permite gestionar más de un tinaco en el futuro
CREATE TABLE IF NOT EXISTS tinacos (
    id          TINYINT UNSIGNED    NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(60)         NOT NULL,
    alto_cm     SMALLINT UNSIGNED   NOT NULL DEFAULT 100,
    ubicacion   VARCHAR(100)                 DEFAULT NULL,
    activo      TINYINT(1)          NOT NULL DEFAULT 1,
    creado_en   DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 3. Tinaco por defecto ──────────────────────────────────────
INSERT INTO tinacos (nombre, alto_cm, ubicacion)
VALUES ('Tinaco Principal', 100, 'UTC – Ramos Arizpe');

-- ── 4. Tabla: mediciones ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS mediciones (
    id              INT UNSIGNED        NOT NULL AUTO_INCREMENT,
    tinaco_id       TINYINT UNSIGNED    NOT NULL DEFAULT 1,
    distancia_cm    DECIMAL(6,2)        NOT NULL,
    porcentaje      TINYINT UNSIGNED    NOT NULL,
    estado          ENUM(
                        'normal',
                        'bajo',
                        'critico',
                        'fuera_de_rango'
                    )                   NOT NULL DEFAULT 'normal',
    creado_en       DATETIME            NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_tinaco   (tinaco_id),
    INDEX idx_fecha    (creado_en),
    CONSTRAINT fk_tinaco
        FOREIGN KEY (tinaco_id) REFERENCES tinacos(id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 5. Usuario de aplicación (solo permisos necesarios) ────────
-- ¡Cambia 'CambiaEstaPassword123!' por una contraseña segura!
CREATE USER IF NOT EXISTS 'medidor_app'@'localhost'
    IDENTIFIED BY 'medidor2025';

GRANT SELECT, INSERT ON medidor_tinaco.tinacos    TO 'medidor_app'@'localhost';
GRANT SELECT, INSERT ON medidor_tinaco.mediciones TO 'medidor_app'@'localhost';

FLUSH PRIVILEGES;

-- ── 6. Vista útil: últimas 50 mediciones con nombre de tinaco ──
CREATE OR REPLACE VIEW v_ultimas_mediciones AS
    SELECT
        m.id,
        t.nombre        AS tinaco,
        m.distancia_cm,
        m.porcentaje,
        m.estado,
        m.creado_en
    FROM mediciones m
    JOIN tinacos    t ON t.id = m.tinaco_id
    ORDER BY m.creado_en DESC
    LIMIT 50;

-- ── 7. Vista: resumen del día actual ──────────────────────────
CREATE OR REPLACE VIEW v_resumen_hoy AS
    SELECT
        t.nombre                        AS tinaco,
        COUNT(m.id)                     AS total_mediciones,
        ROUND(AVG(m.porcentaje), 1)     AS promedio_pct,
        MAX(m.porcentaje)               AS maximo_pct,
        MIN(m.porcentaje)               AS minimo_pct,
        MAX(m.creado_en)                AS ultima_lectura
    FROM mediciones m
    JOIN tinacos    t ON t.id = m.tinaco_id
    WHERE DATE(m.creado_en) = CURDATE()
    GROUP BY t.nombre;
