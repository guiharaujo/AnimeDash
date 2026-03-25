IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'AnimeDash')
BEGIN
    CREATE DATABASE AnimeDash;
END
GO

USE AnimeDash;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Animes')
BEGIN
    CREATE TABLE Animes (
        id              INT             PRIMARY KEY,
        titulo          NVARCHAR(255)   NOT NULL,
        titulo_original NVARCHAR(255),
        generos         NVARCHAR(500),
        nota            FLOAT,
        popularidade    INT,
        episodios       INT,
        status          NVARCHAR(50),
        temporada       NVARCHAR(20),
        ano             INT,
        estudio         NVARCHAR(255),
        descricao       NVARCHAR(MAX),
        capa_url        NVARCHAR(500)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tags')
BEGIN
    CREATE TABLE Tags (
        id        INT           PRIMARY KEY,
        nome      NVARCHAR(255) NOT NULL,
        descricao NVARCHAR(MAX)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Anime_Tags')
BEGIN
    CREATE TABLE Anime_Tags (
        id_anime INT NOT NULL,
        id_tag   INT NOT NULL,
        rank     INT,
        PRIMARY KEY (id_anime, id_tag),
        FOREIGN KEY (id_anime) REFERENCES Animes(id),
        FOREIGN KEY (id_tag)   REFERENCES Tags(id)
    );
END
GO
