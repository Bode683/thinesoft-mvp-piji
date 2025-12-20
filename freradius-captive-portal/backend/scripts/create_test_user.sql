-- Création d'un utilisateur test
INSERT INTO radcheck (username, attribute, op, value) VALUES
('testuser', 'Cleartext-Password', ':=', 'testpassword');

-- Création d'un utilisateur admin
INSERT INTO radcheck (username, attribute, op, value) VALUES
('admin', 'Cleartext-Password', ':=', 'adminpassword');
