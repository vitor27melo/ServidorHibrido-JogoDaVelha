-- SQLite
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome varchar(50) NOT NULL,
    senha varchar(50) NOT NULL,
    status varchar(10) NOT NULL DEFAULT "inativo"
);