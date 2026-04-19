import express from 'express';
import { getUserReports, getScoreTrend, getSkillStats, getDashboardAggregate } from '../controllers/analyticsController.js';

const router = express.Router();

router.get('/', getDashboardAggregate);
router.get('/reports/:userId', getUserReports);
router.get('/trend/:userId', getScoreTrend);
router.get('/skills/:userId', getSkillStats);

export default router;
