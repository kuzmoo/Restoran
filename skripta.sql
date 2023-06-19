CREATE DATABASE restoran;

USE restoran;

CREATE TABLE radnici (
  id INT PRIMARY KEY AUTO_INCREMENT,
  ime_prezime VARCHAR(255) NOT NULL,
  pozicija VARCHAR(255) NOT NULL,
  slika LONGBLOB
);

CREATE TABLE jelovnik (
  id INT PRIMARY KEY AUTO_INCREMENT,
  naziv VARCHAR(255) NOT NULL,
  opis TEXT,
  cijena DECIMAL(10, 2) NOT NULL,
  slika LONGBLOB
);

CREATE TABLE recenzija (
  id INT PRIMARY KEY AUTO_INCREMENT,
  ime_prezime VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  poruka TEXT NOT NULL,
  ocjena INT NOT NULL
);

CREATE TABLE rezervacija (
  id INT PRIMARY KEY AUTO_INCREMENT,
  ime_prezime VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  broj_telefona VARCHAR(20) NOT NULL,
  datum DATE NOT NULL,
  vrijeme TIME NOT NULL,
  broj_gostiju INT NOT NULL,
  poruka TEXT,
  tip_rezervacije ENUM('jednostavna', 'posebna', 'grupna') NOT NULL
);

CREATE TABLE kontakt (
  id INT PRIMARY KEY AUTO_INCREMENT,
  ime_prezime VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  naslov VARCHAR(255) NOT NULL,
  poruka TEXT NOT NULL
);

CREATE TABLE login (
  id INT PRIMARY KEY AUTO_INCREMENT,
  korisnicko_ime VARCHAR(255) NOT NULL,
  ime_prezime VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  sifra VARCHAR(255) NOT NULL
);

-- Veza između logina i recenzija
ALTER TABLE recenzija
ADD COLUMN login_id INT,
ADD FOREIGN KEY (login_id) REFERENCES login(id);

-- Veza između logina i rezervacija
ALTER TABLE rezervacija
ADD COLUMN login_id INT,
ADD FOREIGN KEY (login_id) REFERENCES login(id);

-- Veza između logina i kontakta
ALTER TABLE kontakt
ADD COLUMN login_id INT,
ADD FOREIGN KEY (login_id) REFERENCES login(id);

ALTER TABLE login
ADD CONSTRAINT unique_username UNIQUE (korisnicko_ime);

ALTER TABLE login
ADD CONSTRAINT unique_email UNIQUE (email);

ALTER TABLE login
ADD COLUMN admin BOOLEAN NOT NULL DEFAULT 0;
