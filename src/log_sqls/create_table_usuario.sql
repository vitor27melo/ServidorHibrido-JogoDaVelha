-- SQLite
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome varchar(50) UNIQUE NOT NULL,
    senha varchar(50) NOT NULL,
    status varchar(10) NOT NULL DEFAULT "inativo",
    em_partida_com varchar(50) DEFAULT "Ninguém",
    vitorias INTEGER DEFAULT 0,
    derrotas INTEGER DEFAULT 0,
    empates INTEGER DEFAULT 0
);


CREATE TABLE convite (
    id_convite INTEGER PRIMARY KEY AUTOINCREMENT,
    convidante varchar(50)  NOT NULL,
    convidado varchar(50) NOT NULL,
    ip_convidante varchar(50) NOT NULL,
    porta_convidante varchar(50) NOT NULL,
    dt_convite datetime DEFAULT current_timestamp,
    status varchar(10) NOT NULL DEFAULT "pendente"
);
