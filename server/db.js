import sqlite3 from 'sqlite3';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const dbPath = path.resolve(__dirname, 'users.db');

const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error("Could not connect to users database", err);
    } else {
        console.log("Connected to users SQLite database");
    }
});

// Initialize Users table
db.run(`
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
`, (err) => {
    if (err) console.error("Error creating users table", err);
});

export default db;
