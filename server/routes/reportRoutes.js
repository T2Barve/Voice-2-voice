import express from 'express';
import { saveReport } from '../controllers/reportController.js';

const router = express.Router();

router.post('/save', saveReport);

export default router;
