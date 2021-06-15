-- SQLite
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome varchar(50) UNIQUE NOT NULL,
    senha varchar(50) NOT NULL,
    status varchar(10) NOT NULL DEFAULT "inativo",
    em_partida_com varchar(50) DEFAULT "Ninguém"
);

CREATE TABLE convite (
    id_convite INTEGER PRIMARY KEY AUTOINCREMENT,
    convidante varchar(50)  NOT NULL,
    convidado varchar(50) NOT NULL,
    ip_convidante varchar(50) NOT NULL,
    porta_convidante varchar(50) NOT NULL,
    status varchar(10) NOT NULL DEFAULT "pendente"
);
