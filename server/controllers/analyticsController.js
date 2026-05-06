import Report from '../models/reportModel.js';

export const getUserReports = async (req, res) => {
  try {
    const { userId } = req.params;
    const reports = await Report.find({ user_id: userId }).sort({ createdAt: -1 });
    res.json(reports);
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
};

export const getScoreTrend = async (req, res) => {
  try {
    const { userId } = req.params;
    const reports = await Report.find({ user_id: userId }).sort({ createdAt: 1 });
    const trend = reports.map(r => ({
      date: r.createdAt,
      score: r.score || 0,
      interview_type: r.interview_type || 'unknown',
      company: r.company || 'Unknown'
    }));
    res.json(trend);
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
};

export const getSkillStats = async (req, res) => {
  try {
    const { userId } = req.params;
    const reports = await Report.find({ user_id: userId });

    if (!reports.length) {
      return res.json({ dsa: 0, communication: 0, problem_solving: 0, system_design: 0, core_cs: 0 });
    }

    let totals = { dsa: 0, communication: 0, problem_solving: 0, system_design: 0, core_cs: 0 };
    let counts = { dsa: 0, communication: 0, problem_solving: 0, system_design: 0, core_cs: 0 };

    reports.forEach(r => {
      const s = r.score || 0;
      const type = (r.interview_type || '').toLowerCase();
      if (type === 'dsa') {
        totals.dsa += s; counts.dsa++;
        totals.problem_solving += s; counts.problem_solving++;
      } else if (type === 'technical') {
        totals.core_cs += s; counts.core_cs++;
        totals.communication += (r.breakdown?.resume_based || s); counts.communication++;
      } else if (type === 'case_study') {
        totals.system_design += s; counts.system_design++;
        totals.communication += (r.breakdown?.resume_based || s); counts.communication++;
      }
    });

    const result = {};
    Object.keys(totals).forEach(k => {
      result[k] = counts[k] > 0 ? parseFloat((totals[k] / counts[k]).toFixed(1)) : 0;
    });

    res.json(result);
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
};

export const getDashboardAggregate = async (req, res) => {
  try {
    const user = req.user;
    const userId = user?.id || user?._id;

    if (!userId) {
      return res.status(401).json({ status: 'error', message: 'Unauthorized' });
    }

    const userIdStr = String(userId);
    console.log(`[Analytics] Fetching for user_id="${userIdStr}"`);

    // STRICT: each user sees ONLY their own reports. No migration, no fallback.
    const reports = await Report.find({ user_id: userIdStr }).sort({ createdAt: -1 });
    console.log(`[Analytics] Found ${reports.length} reports`);

    let avg = 0;
    if (reports.length > 0) {
      const sum = reports.reduce((acc, r) => acc + (r.score || 0), 0);
      avg = parseFloat((sum / reports.length).toFixed(1));
    }

    const recent = reports.slice(0, 5).map(r => ({
      type: r.interview_type || 'Interview',
      company: r.company || 'Unknown',
      date: r.createdAt ? new Date(r.createdAt).toLocaleDateString('en-IN') : 'N/A',
      score: parseFloat((r.score || 0).toFixed(1))
    }));

    // Score trend — chronological, last 10 sessions
    const score_trend = [...reports].reverse().slice(-10).map(r => ({
      date: r.createdAt ? new Date(r.createdAt).toLocaleDateString('en-IN') : '',
      score: parseFloat((r.score || 0).toFixed(1)),
      type: r.interview_type || 'Interview'
    }));

    // Real skill breakdown — one score per interview type (most recent)
    const skillBreakdown = { dsa: null, technical: null, case_study: null };
    reports.forEach(r => {
      const type = (r.interview_type || '').toLowerCase();
      if (type === 'dsa'        && skillBreakdown.dsa       === null) skillBreakdown.dsa       = parseFloat((r.score || 0).toFixed(1));
      if (type === 'technical'  && skillBreakdown.technical  === null) skillBreakdown.technical  = parseFloat((r.score || 0).toFixed(1));
      if (type === 'case_study' && skillBreakdown.case_study === null) skillBreakdown.case_study = parseFloat((r.score || 0).toFixed(1));
    });

    res.json({
      status: 'success',
      data: {
        total_interviews: reports.length,
        average_score: avg,
        recent_sessions: recent,
        score_trend,
        skill_breakdown: skillBreakdown
      }
    });

  } catch (err) {
    console.error('[Analytics] Error:', err.message);
    res.status(500).json({ status: 'error', message: 'Failed to fetch analytics' });
  }
};
