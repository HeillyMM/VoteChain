-- ============================================================
--  init_final.sql
--  Sistema de Votación Electrónica — Bolivia
--  Versión normalizada 3FN
--
--  IMPORTANTE: segip_db y tse_db son bases de datos de
--  instituciones distintas. NO tienen Foreign Keys entre sí.
--  La única comunicación es mediante la API REST del SEGIP.
--  El campo CI aparece en ambas pero como dato independiente,
--  nunca como referencia cruzada.
-- ============================================================

-- ─── Bases de datos ──────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS segip_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS tse_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ─── Usuarios de aplicación ──────────────────────────────────
CREATE USER IF NOT EXISTS 'segip_user'@'%' IDENTIFIED BY 'segip_pass';
GRANT ALL PRIVILEGES ON segip_db.* TO 'segip_user'@'%';

CREATE USER IF NOT EXISTS 'tse_user'@'%' IDENTIFIED BY 'tse_pass';
GRANT ALL PRIVILEGES ON tse_db.* TO 'tse_user'@'%';

-- segip_user NO tiene acceso a tse_db
-- tse_user NO tiene acceso a segip_db
FLUSH PRIVILEGES;


-- ============================================================
--  SEGIP_DB
--  Institución: Servicio General de Identificación Personal
--  Responsabilidad: solo identidad ciudadana
--  Comunicación externa: expone API REST autenticada
--  NO conoce elecciones, candidatos ni votos
-- ============================================================
USE segip_db;

CREATE TABLE IF NOT EXISTS departamentos (
    id     TINYINT     NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_departamento (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO departamentos (nombre) VALUES
('LA PAZ'),('COCHABAMBA'),('SANTA CRUZ'),('ORURO'),
('POTOSI'),('TARIJA'),('CHUQUISACA'),('BENI'),('PANDO');

-- ── Ciudadanos ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ciudadanos (
    id                INT          NOT NULL AUTO_INCREMENT,
    ci                VARCHAR(12)  NOT NULL,
    complemento       VARCHAR(4)   NULL,
    nombres           VARCHAR(100) NOT NULL,
    apellido_paterno  VARCHAR(80)  NOT NULL,
    apellido_materno  VARCHAR(80)  NULL,
    fecha_nacimiento  DATE         NOT NULL,
    lugar_nacimiento  VARCHAR(120) NULL,
    sexo              ENUM('M','F') NOT NULL,
    estado_civil      ENUM('SOLTERO','CASADO','DIVORCIADO',
                           'VIUDO','UNION_LIBRE') NULL,
    departamento_id   TINYINT      NOT NULL,
    municipio         VARCHAR(80)  NULL,
    domicilio         VARCHAR(200) NULL,
    vivo              TINYINT(1)   NOT NULL DEFAULT 1,
    activo            TINYINT(1)   NOT NULL DEFAULT 1,
    observaciones     TEXT         NULL,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_ci (ci),
    INDEX idx_ci (ci),
    CONSTRAINT fk_ciudadano_depto FOREIGN KEY (departamento_id)
        REFERENCES departamentos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Biometría (tabla separada, acceso muy restringido) ───────
-- La API NUNCA expone estos datos al TSE
CREATE TABLE IF NOT EXISTS biometria (
    ciudadano_id  INT         NOT NULL,
    foto_hash     VARCHAR(64) NULL,
    huella_hash   VARCHAR(64) NULL,
    updated_at    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                              ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (ciudadano_id),
    CONSTRAINT fk_bio_ciudadano FOREIGN KEY (ciudadano_id)
        REFERENCES ciudadanos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── API Keys ─────────────────────────────────────────────────
-- El TSE debe presentar su api_key en cada consulta
-- Si la key no existe o está inactiva, la respuesta es 401
CREATE TABLE IF NOT EXISTS api_keys (
    id            INT          NOT NULL AUTO_INCREMENT,
    sistema       VARCHAR(50)  NOT NULL,
    api_key_hash  VARCHAR(64)  NOT NULL,
    activo        TINYINT(1)   NOT NULL DEFAULT 1,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_api_key (api_key_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Api key inicial del TSE (hash de 'TSE-SECRET-KEY-2025')
-- En producción generar con secrets.token_hex(32)
INSERT IGNORE INTO api_keys (sistema, api_key_hash, activo) VALUES
('TSE', SHA2('TSE-SECRET-KEY-2025', 256), 1);


-- ============================================================
--  TSE_DB
--  Institución: Tribunal Supremo Electoral
--  Responsabilidad: gestión del proceso electoral
--  Comunicación externa: consume API REST del SEGIP
--  NO tiene Foreign Keys hacia segip_db
--  NO almacena votos individuales (van en la blockchain)
-- ============================================================
USE tse_db;

-- ── Departamentos (catálogo propio, independiente del SEGIP) ─
CREATE TABLE IF NOT EXISTS departamentos (
    id     TINYINT     NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_departamento (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO departamentos (nombre) VALUES
('LA PAZ'),('COCHABAMBA'),('SANTA CRUZ'),('ORURO'),
('POTOSI'),('TARIJA'),('CHUQUISACA'),('BENI'),('PANDO');

-- ── Roles ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS roles (
    id          INT         NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(30) NOT NULL,
    descripcion TEXT        NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_rol (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO roles (nombre, descripcion) VALUES
('ADMIN',    'Administrador TSE. Crea elecciones y candidatos.'),
('OPERADOR', 'Operador de mesa. Verifica identidad y habilita kioscos.'),
('AUDITOR',  'Solo lectura. Accede a la cadena pública y resultados.');

-- ── Recintos ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recintos (
    id              INT          NOT NULL AUTO_INCREMENT,
    codigo          VARCHAR(20)  NOT NULL,
    nombre          VARCHAR(150) NOT NULL,
    direccion       VARCHAR(200) NULL,
    municipio       VARCHAR(80)  NOT NULL,
    departamento_id TINYINT      NOT NULL,
    total_mesas     INT          NOT NULL DEFAULT 1,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (id),
    UNIQUE KEY uq_codigo_recinto (codigo),
    CONSTRAINT fk_recinto_depto FOREIGN KEY (departamento_id)
        REFERENCES departamentos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Usuarios TSE ─────────────────────────────────────────────
-- Funcionarios del TSE. No son ciudadanos del padrón.
CREATE TABLE IF NOT EXISTS usuarios (
    id             INT          NOT NULL AUTO_INCREMENT,
    ci             VARCHAR(12)  NOT NULL,
    nombres        VARCHAR(100) NOT NULL,
    apellidos      VARCHAR(160) NOT NULL,
    email          VARCHAR(120) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    rol_id         INT          NOT NULL,
    recinto_id     INT          ,
    activo         TINYINT(1)   NOT NULL DEFAULT 1,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_ci_usuario (ci),
    UNIQUE KEY uq_email (email),
    INDEX idx_rol (rol_id),
    CONSTRAINT fk_usuario_rol FOREIGN KEY (rol_id)
        REFERENCES roles (id),
    CONSTRAINT fk_usuario_recinto 
    FOREIGN KEY (recinto_id) REFERENCES recintos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ── Kioscos ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS kioscos (
    id            INT         NOT NULL AUTO_INCREMENT,
    recinto_id    INT         NOT NULL,
    nombre        VARCHAR(50) NOT NULL,
    ip_local      VARCHAR(15) NULL,
    activo        TINYINT(1)  NOT NULL DEFAULT 1,
    ultimo_uso    DATETIME    NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_kiosco_recinto (recinto_id, nombre),
    CONSTRAINT fk_kiosco_recinto FOREIGN KEY (recinto_id)
        REFERENCES recintos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Elecciones ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS elecciones (
    id                INT          NOT NULL AUTO_INCREMENT,
    codigo            VARCHAR(30)  NOT NULL,
    titulo            VARCHAR(200) NOT NULL,
    descripcion       TEXT         NULL,
    tipo              ENUM('PRESIDENCIAL','MUNICIPAL','DEPARTAMENTAL',
                           'REFERENDUM','ASAMBLEA') NOT NULL,
    estado            ENUM('CONFIGURACION','ACTIVA',
                           'SUSPENDIDA','CERRADA')
                                   NOT NULL DEFAULT 'CONFIGURACION',
    fecha_inicio      DATETIME     NOT NULL,
    fecha_fin         DATETIME     NULL,
    clave_publica_pem TEXT         NULL,
    clave_privada_pem TEXT         NULL,
    created_by        INT          NULL,
    created_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                   ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_codigo_eleccion (codigo),
    CONSTRAINT fk_eleccion_creador FOREIGN KEY (created_by)
        REFERENCES usuarios (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recintos_elecciones(
    recinto_id INT NOT NULL,
    eleccion_id INT NOT NULL,
    PRIMARY KEY (recinto_id,eleccion_id),
    CONSTRAINT fk_id_recinto FOREIGN KEY (recinto_id)
    REFERENCES recintos (id),
    CONSTRAINT fk_id_eleccion FOREIGN KEY (eleccion_id)
    REFERENCES elecciones (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;;



-- ── Padrón Electoral ─────────────────────────────────────────
-- Construido consultando la API del SEGIP antes de la elección.
-- El campo CI es dato copiado del SEGIP, NO es FK hacia segip_db.
-- Solo registra SI votó, NUNCA A QUIÉN votó.
CREATE TABLE IF NOT EXISTS padron_electoral (
    id                    INT          NOT NULL AUTO_INCREMENT,

    -- CI copiada del SEGIP al construir el padrón.
    -- Es un dato, no una FK. El SEGIP y el TSE son independientes.
    ci                    VARCHAR(12)  NOT NULL,
    complemento           VARCHAR(4)   NULL,

    nombres               VARCHAR(100) NOT NULL,
    apellido_paterno      VARCHAR(80)  NOT NULL,
    apellido_materno      VARCHAR(80)  NULL,
    fecha_nacimiento      DATE         NOT NULL,
    sexo                  ENUM('M','F') NOT NULL,

    recinto_id            INT,
    mesa_numero           INT,

    habilitado            TINYINT(1)   NOT NULL DEFAULT 1,
    motivo_inhabilitacion VARCHAR(200) NULL,

    -- Sabe QUE votó, NUNCA A QUIÉN
    ya_voto               TINYINT(1)   NOT NULL DEFAULT 0,
    departamento_id       TINYINT      NOT NULL,
    eleccion_id           INT          NOT NULL,
    hora_voto             DATETIME     NULL,
    habilitado_por        INT          NULL,

    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                       ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_ci_padron (ci),
    INDEX idx_recinto_mesa (recinto_id, mesa_numero),
    CONSTRAINT fk_padron_recinto  FOREIGN KEY (recinto_id)
        REFERENCES recintos (id),
    CONSTRAINT fk_padron_departamento  FOREIGN KEY (departamento_id)
        REFERENCES departamentos (id),
    CONSTRAINT fk_padron_eleccion  FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id),
    CONSTRAINT fk_padron_operador FOREIGN KEY (habilitado_por)
        REFERENCES usuarios (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Sesiones de Kiosco ───────────────────────────────────────
-- Token de un solo uso con expiración de 5 minutos.
-- Se destruye en cuanto el voto es emitido.
CREATE TABLE IF NOT EXISTS sesiones_kiosco (
    id           INT         NOT NULL AUTO_INCREMENT,
    operador_id  INT         NOT NULL,
    padron_id    INT         NOT NULL,
    kiosco_id    INT         NOT NULL,
    token_hash   VARCHAR(64) NOT NULL,
    estado       ENUM('PENDIENTE','ACTIVA','COMPLETADA','EXPIRADA')
                             NOT NULL DEFAULT 'PENDIENTE',
    expira_en    DATETIME    NOT NULL,
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_token (token_hash),
    INDEX idx_estado_sesion (estado),
    CONSTRAINT fk_sesion_operador FOREIGN KEY (operador_id)
        REFERENCES usuarios (id),
    CONSTRAINT fk_sesion_padron   FOREIGN KEY (padron_id)
        REFERENCES padron_electoral (id),
    CONSTRAINT fk_sesion_kiosco   FOREIGN KEY (kiosco_id)
        REFERENCES kioscos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Candidatos ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidatos (
    id                       INT          NOT NULL AUTO_INCREMENT,
    eleccion_id              INT          NOT NULL,
    numero_lista             INT          NOT NULL,
    sigla_partido            VARCHAR(20)  NOT NULL,
    nombre_partido           VARCHAR(150) NULL,
    nombres                  VARCHAR(100) NOT NULL,
    apellido_paterno         VARCHAR(80)  NOT NULL,
    apellido_materno         VARCHAR(80)  NULL,
    formula_nombres          VARCHAR(100) NULL,
    formula_apellido_paterno VARCHAR(80)  NULL,
    logo_partido             VARCHAR(200) NULL,
    foto_candidato           VARCHAR(200) NULL,
    color_partido            VARCHAR(7)   NULL,
    propuesta_breve          TEXT         NULL,
    activo                   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_candidato_lista (eleccion_id, numero_lista),
    CONSTRAINT fk_candidato_eleccion FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Índice de Bloques ────────────────────────────────────────
-- Solo metadatos. Los votos viven en blockchain_data/chain.json
-- Esta tabla permite búsquedas rápidas sin leer el archivo JSON.
CREATE TABLE IF NOT EXISTS blockchain_bloques (
    id           INT         NOT NULL AUTO_INCREMENT,
    eleccion_id  INT         NOT NULL,
    block_index  INT         NOT NULL,
    prev_hash    VARCHAR(64) NOT NULL,
    block_hash   VARCHAR(64) NOT NULL,
    merkle_root  VARCHAR(64) NOT NULL,
    total_tx     INT         NOT NULL DEFAULT 0,
    nonce        INT         NOT NULL DEFAULT 0,
    timestamp    DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_block_hash (block_hash),
    UNIQUE KEY uq_block_index_eleccion (eleccion_id, block_index),
    INDEX idx_prev_hash (prev_hash),
    CONSTRAINT fk_bloque_eleccion FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Recibos ──────────────────────────────────────────────────
-- El votante recibe un código para verificar que su bloque
-- existe en la cadena. No revela a quién votó.
CREATE TABLE IF NOT EXISTS recibos (
    id             INT         NOT NULL AUTO_INCREMENT,
    padron_id      INT         NOT NULL,
    eleccion_id    INT         NOT NULL,
    codigo_recibo  VARCHAR(32) NOT NULL,
    block_hash     VARCHAR(64) NOT NULL,
    impreso        TINYINT(1)  NOT NULL DEFAULT 0,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_codigo_recibo (codigo_recibo),
    UNIQUE KEY uq_padron_eleccion (padron_id, eleccion_id),
    CONSTRAINT fk_recibo_padron   FOREIGN KEY (padron_id)
        REFERENCES padron_electoral (id),
    CONSTRAINT fk_recibo_eleccion FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Conteo Rápido ────────────────────────────────────────────
-- Totales por candidato. Se actualiza al descifrar la blockchain.
-- El porcentaje se calcula en Python, nunca se almacena.
CREATE TABLE IF NOT EXISTS conteos (
    id           INT      NOT NULL AUTO_INCREMENT,
    eleccion_id  INT      NOT NULL,
    candidato_id INT      NULL,
    tipo         ENUM('VALIDO','BLANCO','NULO') NOT NULL,
    total_votos  INT      NOT NULL DEFAULT 0,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                          ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_conteo (eleccion_id, candidato_id, tipo),
    CONSTRAINT fk_conteo_eleccion  FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id) ON DELETE CASCADE,
    CONSTRAINT fk_conteo_candidato FOREIGN KEY (candidato_id)
        REFERENCES candidatos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Audit Log ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id               BIGINT      NOT NULL AUTO_INCREMENT,
    usuario_id       INT         NULL,
    eleccion_id      INT         NULL,
    accion           VARCHAR(50) NOT NULL,
    descripcion      TEXT        NULL,
    ip_hash          VARCHAR(64) NULL,
    hash_integridad  VARCHAR(64) NOT NULL,
    created_at       DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_usuario_audit  (usuario_id),
    INDEX idx_eleccion_audit (eleccion_id),
    INDEX idx_accion_audit   (accion),
    CONSTRAINT fk_audit_usuario  FOREIGN KEY (usuario_id)
        REFERENCES usuarios (id) ON DELETE SET NULL,
    CONSTRAINT fk_audit_eleccion FOREIGN KEY (eleccion_id)
        REFERENCES elecciones (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;



--- llenando base de datos

USE tse_db;

INSERT INTO recintos
(codigo,nombre,direccion,municipio,departamento_id,total_mesas,activo)
VALUES
('LP001','Unidad Educativa Bolívar','Av. Principal 123','Viacha',1,10,1),
('LP002','Colegio Mariscal Sucre','Zona Central','Achacachi',1,8,1),
('CB001','Unidad Educativa Cochabamba','Av. Aroma','Cercado',2,12,1),
('SC001','Colegio Montero Norte','Zona Norte','Montero',3,15,1),
('SC002','Unidad Educativa Warnes','Av. Warnes','Warnes',3,10,1),
('OR001','Colegio Huanuni','Zona Minera','Huanuni',4,7,1),
('PT001','Unidad Educativa Potosí','Zona Central','Potosi',5,9,1),
('TJ001','Colegio Tarija Sur','Av. La Banda','Tarija',6,8,1),
('CH001','Unidad Educativa Sucre','Av. Hernando Siles','Sucre',7,12,1),
('BE001','Colegio Trinidad','Zona Central','Trinidad',8,6,1),
('PA001','Unidad Educativa Cobija','Av. Internacional','Cobija',9,5,1),
('SC003','Colegio Plan 3000','Plan 3000','Santa Cruz',3,18,1);

INSERT INTO usuarios
(ci,nombres,apellidos,email,password_hash,rol_id,activo)
VALUES
('16564359','Helen Keilly','Mamani Mollinedo','helenkeylli@gmail.com','$2b$12$4jeFssNNinyNNoQA0HpY/uJZdDPlrjhUnUEQsl9FcmAe1EW8YBury',1,1),
('64155610','Limber Limachi','Perez','limberlimachi@gmail.com','$2b$12$4jeFssNNinyNNoQA0HpY/uJZdDPlrjhUnUEQsl9FcmAe1EW8YBury',2,1),
('79124712','Melany Aidee','Gonzales','melanyaidee@gmail.com','$2b$12$4jeFssNNinyNNoQA0HpY/uJZdDPlrjhUnUEQsl9FcmAe1EW8YBury',3,1);

INSERT INTO elecciones
(codigo,titulo,descripcion,tipo,estado,fecha_inicio,fecha_fin,created_by)
VALUES
('PRES2026','Elección Presidencial 2026','Elección general presidencial','PRESIDENCIAL','CONFIGURACION','2026-07-01 08:00:00','2026-07-01 18:00:00',1),
('MUNI2026','Elección Municipal 2026','Elección de alcaldes','MUNICIPAL','CONFIGURACION','2026-08-15 08:00:00','2026-08-15 18:00:00',1),
('REF2026','Referéndum Nacional 2026','Consulta ciudadana','REFERENDUM','CONFIGURACION','2026-09-10 08:00:00','2026-09-10 18:00:00',1);

INSERT INTO recintos_elecciones
(recinto_id,eleccion_id)
VALUES
(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(1,2),(3,2),(5,2),(7,2),(9,2),(2,3),(4,3),(6,3),(8,3),(10,3),(11,3);

INSERT INTO kioscos
(recinto_id,nombre,activo)
VALUES
(1,'KIOSCO-1',1),
(1,'KIOSCO-2',1),
(2,'KIOSCO-1',1),
(3,'KIOSCO-1',1),
(3,'KIOSCO-2',1),
(4,'KIOSCO-1',1),
(5,'KIOSCO-1',1),
(6,'KIOSCO-1',1),
(7,'KIOSCO-1',1),
(8,'KIOSCO-1',1),
(9,'KIOSCO-1',1),
(10,'KIOSCO-1',1),
(11,'KIOSCO-1',1),
(12,'KIOSCO-1',1);


INSERT INTO candidatos
(eleccion_id,numero_lista,sigla_partido,nombre_partido,nombres,apellido_paterno,apellido_materno,activo)
VALUES
(1,1,'MAS','Movimiento al Socialismo','Luis','Arce','Catacora',1),
(1,2,'CC','Comunidad Ciudadana','Carlos','Mesa','Gisbert',1),
(1,3,'LIBRE','Libre Bolivia','Jorge','Quiroga','Ramirez',1);


INSERT INTO candidatos
(eleccion_id,numero_lista,sigla_partido,nombre_partido,nombres,apellido_paterno,apellido_materno,activo)
VALUES
(2,1,'SUMATE','SUMATE','Manfred','Reyes','Villa',1),
(2,2,'UCS','Unidad Civica','Jhonny','Fernandez','Saucedo',1),
(2,3,'MTS','Movimiento Tercer Sistema','Felix','Patzi','Paco',1);