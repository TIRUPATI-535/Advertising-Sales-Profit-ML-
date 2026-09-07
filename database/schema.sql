
-- ================================
-- USERS TABLE
-- ================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ================================
-- PREDICTIONS TABLE
-- ================================

CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id)ON DELETE CASCADE,
    tv FLOAT NOT NULL,
    radio FLOAT NOT NULL,
    newspaper FLOAT NOT NULL,
    predicted_sales FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);
