CREATE DATABASE IF NOT EXISTS shopsight;
USE shopsight;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(200) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS businesses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    type VARCHAR(100) NOT NULL,
    years INT DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'INR',
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    cost DECIMAL(12,2) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    quantity INT NOT NULL,
    stock INT NOT NULL,
    expiry DATE NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    product_name VARCHAR(150) NOT NULL,
    units INT NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    cost DECIMAL(12,2) NOT NULL,
    sale_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_products_user
ON products(user_id);

CREATE INDEX idx_sales_user
ON sales(user_id);

CREATE INDEX idx_sales_date
ON sales(sale_date);
