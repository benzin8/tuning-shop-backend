CREATE DATABASE IF NOT EXISTS tuning_shop CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tuning_shop;

INSERT IGNORE INTO roles (role_name) VALUES ('admin'), ('customer');

INSERT IGNORE INTO order_statuses (status_name)
VALUES ('pending'), ('confirmed'), ('processing'), ('shipped'), ('delivered'), ('cancelled');
