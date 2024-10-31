-- This script initialises the db user and password
ALTER USER 'root'@'172.18.0.1' IDENTIFIED BY 'passwordtest123';
CREATE USER 'testuser'@'172.18.0.1' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON `4050Backend`.* TO 'testuser'@'172.18.0.1';
FLUSH PRIVILEGES;
