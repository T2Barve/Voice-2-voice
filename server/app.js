import express from 'express';
import cors from 'cors';
import interviewRoutes from './routes/interviewRoutes.js';
import reportRoutes from './routes/reportRoutes.js';
import analyticsRoutes from './routes/analyticsRoutes.js';
import authRoutes from './routes/authRoutes.js';
import resumeRoutes from './routes/resumeRoutes.js';
import jobRoutes from './routes/jobRoutes.js';
import authMiddleware from './middleware/authMiddleware.js';
import { errorHandler } from './middleware/errorHandler.js';

const app = express();

app.use(cors({
  origin: ["http://localhost:5173", "http://localhost:5174"],
  credentials: true
}));
app.use(express.json());

// Public Auth routes
app.use('/api/auth', authRoutes);

// Protected routes (as mandated to be bulletproof)
app.use('/api/resume', authMiddleware, resumeRoutes);

// Protected routes (as mandated to be bulletproof)
app.use('/api/dsa', authMiddleware, interviewRoutes);
app.use('/api/technical', authMiddleware, interviewRoutes);
app.use('/api/case-study', authMiddleware, interviewRoutes);

app.use('/api/report', authMiddleware, reportRoutes);
app.use('/api/analytics', authMiddleware, analyticsRoutes);
app.use('/api/jobs', authMiddleware, jobRoutes);

// Error Middleware
app.use(errorHandler);

export default app;
