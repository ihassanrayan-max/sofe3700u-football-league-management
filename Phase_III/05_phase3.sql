USE group12_football_phase2;
CREATE TABLE IF NOT EXISTS login_credentials (
  user_id INT PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS imported_matches (
  external_id INT PRIMARY KEY,
  match_id INT NOT NULL UNIQUE,
  FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS web_sessions (
  session_id CHAR(64) PRIMARY KEY,
  user_id INT NOT NULL,
  expires_at DATETIME NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
