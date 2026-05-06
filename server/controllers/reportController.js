import Report from "../models/reportModel.js";

/**
 * Normalizes incoming report payload from Python workflows before saving.
 * Handles field name mismatches between workflow output and Mongoose schema.
 */
function normalizePayload(body) {
  const normalized = { ...body };

  // Fix: Python workflows send "type" instead of "interview_type"
  if (!normalized.interview_type && normalized.type) {
    normalized.interview_type = normalized.type;
  }
  delete normalized.type;

  // Fix: Technical/Case-Study send "total_score" instead of "score"
  if (normalized.total_score !== undefined && normalized.score === undefined) {
    normalized.score = normalized.total_score;
  }
  delete normalized.total_score;

  // Fix: Ensure score is a number
  if (normalized.score !== undefined) {
    normalized.score = parseFloat(normalized.score) || 0;
  }

  // Fix: strengths/weaknesses should be arrays of strings
  if (typeof normalized.strengths === 'string') {
    normalized.strengths = [normalized.strengths];
  }
  if (typeof normalized.weaknesses === 'string') {
    normalized.weaknesses = [normalized.weaknesses];
  }

  return normalized;
}

/**
 * Saves a detailed interview report to MongoDB with robust logging and error handling.
 */
export const saveReport = async (req, res) => {
  try {
    console.log("[Report] Incoming report — normalizing payload...");

    const payload = normalizePayload(req.body);

    console.log("[Report] Normalized Payload:");
    console.log(JSON.stringify(payload, null, 2));

    // Validate minimal requirements
    if (!payload.session_id || !payload.user_id) {
      console.error("[Report] Validation Failed: Missing session_id or user_id");
      return res.status(400).json({
        success: false,
        message: "Missing mandatory session_id or user_id"
      });
    }

    const report = await Report.create(payload);

    console.log("[Report] Saved to MongoDB. ID:", report._id);
    console.log(`   user_id: ${report.user_id} | type: ${report.interview_type} | score: ${report.score}`);

    res.status(201).json({ success: true, data: report });

  } catch (error) {
    console.error("[Report] MongoDB Save Error:", error.message);
    res.status(500).json({
      success: false,
      message: error.message,
      detail: "Check if the payload matches the Mongoose schema. Common issues: missing user_id, score not a number."
    });
  }
};
