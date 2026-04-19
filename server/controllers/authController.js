import db from '../db.js';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'fallback_secret_key_change_in_production';

export const signup = async (req, res) => {
    const { name, email, password } = req.body;
    
    if (!name || !email || !password) {
        return res.status(400).json({ error: 'All fields are required' });
    }

    try {
        // Must use bcrypt.hash() (salt >= 10)
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        db.run(`INSERT INTO users (name, email, password) VALUES (?, ?, ?)`, [name, email, hashedPassword], function(err) {
            if (err) {
                if (err.message.includes('UNIQUE')) {
                    return res.status(400).json({ error: 'Email already exists' });
                }
                return res.status(500).json({ error: 'Database error' });
            }

            const token = jwt.sign({ id: this.lastID, email }, JWT_SECRET, { expiresIn: '7d' });
            res.status(201).json({ message: 'User created successfully', token });
        });
    } catch (error) {
        res.status(500).json({ error: 'Server error' });
    }
};

export const login = async (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ error: 'All fields are required' });
    }

    db.get(`SELECT * FROM users WHERE email = ?`, [email], async (err, user) => {
        if (err) return res.status(500).json({ error: 'Database error' });
        if (!user) return res.status(400).json({ error: 'Invalid credentials' });

        const isMatch = await bcrypt.compare(password, user.password);
        if (!isMatch) return res.status(400).json({ error: 'Invalid credentials' });

        const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
        res.json({ message: 'Login successful', token, user: { id: user.id, name: user.name, email: user.email }});
    });
};

export const me = (req, res) => {
    db.get(`SELECT id, name, email FROM users WHERE id = ?`, [req.user.id], (err, user) => {
        if (err) return res.status(500).json({ error: 'Database error' });
        if (!user) return res.status(404).json({ error: 'User not found' });
        
        // Exact format required by strict prompt
        res.json({
            id: user.id,
            name: user.name,
            email: user.email
        });
    });
};
