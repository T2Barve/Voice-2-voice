import Report from '../models/reportModel.js';

export const getUserReports = async (req, res) => {
  const { userId } = req.params;
  const reports = await Report.find({ user_id: userId }).sort({ created_at: -1 });
  res.json(reports);
};

export const getScoreTrend = async (req, res) => {
  const { userId } = req.params;
  const reports = await Report.find({ user_id: userId }).sort({ created_at: 1 });

  const trend = reports.map(r => ({
    date: r.created_at,
    score: r.score
  }));

  res.json(trend);
};

export const getSkillStats = async (req, res) => {
  const { userId } = req.params;
  const reports = await Report.find({ user_id: userId });

  let totals = {
    dsa: 0,
    communication: 0,
    problem_solving: 0,
    system_design: 0,
    core_cs: 0
  };

  reports.forEach(r => {
    Object.keys(totals).forEach(k => {
      totals[k] += r.skills[k] || 0;
    });
  });

  const count = reports.length || 1;

  Object.keys(totals).forEach(k => {
    totals[k] = totals[k] / count;
  });

  res.json(totals);
};

export const getDashboardAggregate = async (req, res) => {
  try {
    const user = req.user; // from authMiddleware
    const userId = user?.id || user?._id;
    if (!userId) {
      return res.status(401).json({ status: 'error', message: 'Unauthorized' });
    }

    const reports = await Report.find({ user_id: userId }).sort({ created_at: -1 });
    
    let avg = 0;
    if (reports.length > 0) {
      const sum = reports.reduce((acc, r) => acc + (r.score || 0), 0);
      avg = (sum / reports.length).toFixed(1);
    }
    
    const recent = reports.slice(0, 5).map(r => ({
      type: r.type || 'Interivew',
      company: r.company || 'Unknown',
      date: new Date(r.created_at).toLocaleDateString(),
      score: (r.score || 0).toFixed(1)
    }));

    res.json({
      status: 'success',
      data: {
        total_interviews: reports.length,
        average_score: avg,
        recent_sessions: recent
      }
    });

  } catch (err) {
    console.error("Dashboard fetch error:", err);
    res.status(500).json({ status: 'error', message: "Failed to fetch analytics" });
  }
};
