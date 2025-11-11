
CREATE TABLE IF NOT EXISTS at.users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_username ON at.users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON at.users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON at.users(is_active);

INSERT INTO at.users (username, email, password_hash) 
VALUES ('ahu', 'huk.artur@gmail.com', 'gAAAAABneXW1NRukIU3msbGjUGZCkg8vq57SQWMfqoo3eIXYI-W1Q_346H-WVHHj5llMXKo6scwc-KxtcUQVBOLEBOMPQuH-tQ==')
ON CONFLICT (username) DO NOTHING;	 

