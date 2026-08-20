CREATE DATABASE IF NOT EXISTS INVENTORY;
USE INVENTORY;

CREATE TABLE IF NOT EXISTS business_profile (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,
    business_type VARCHAR(100) NOT NULL,
    years_in_operation INT NOT NULL,
    currency VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    cost DECIMAL(10,2) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL,
    expiry_date DATE NOT NULL,
    in_shop TINYINT(1) NOT NULL DEFAULT 0,
    current_units INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_products_name (name),
    INDEX idx_products_shop (in_shop)
);

CREATE TABLE IF NOT EXISTS sales (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sale_date DATE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    units_sold INT NOT NULL,
    sale_price DECIMAL(10,2) NOT NULL,
    unit_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sales_date (sale_date),
    INDEX idx_sales_product (product_name)
);
