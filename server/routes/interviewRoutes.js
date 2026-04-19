import express from 'express';
import {
  startDSAInterview,
  submitDSAAnswer,
  startTechnicalInterview,
  submitTechnicalAnswer,
  startCaseStudyInterview,
  submitCaseStudyAnswer
} from '../controllers/interviewController.js';

const router = express.Router();

// These are mounted on /api/dsa, /api/technical, and /api/case-study respectively in app.js
router.post('/start', (req, res, next) => {
  // Determine which specific controller function to call based on the original path
  if (req.originalUrl.includes('/dsa')) return startDSAInterview(req, res, next);
  if (req.originalUrl.includes('/technical')) return startTechnicalInterview(req, res, next);
  if (req.originalUrl.includes('/case-study')) return startCaseStudyInterview(req, res, next);
  next();
});

router.post('/submit', (req, res, next) => {
  if (req.originalUrl.includes('/dsa')) return submitDSAAnswer(req, res, next);
  if (req.originalUrl.includes('/technical')) return submitTechnicalAnswer(req, res, next);
  if (req.originalUrl.includes('/case-study')) return submitCaseStudyAnswer(req, res, next);
  next();
});

export default router;
