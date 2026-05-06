import express from 'express';
import { searchJobs } from '../controllers/jobController.js';
import authMiddleware from '../middleware/authMiddleware.js';

const router = express.Router();

// Protected route: Only logged in users can search jobs
router.get('/search', authMiddleware, searchJobs);

export default router;
