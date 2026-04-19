import Report from "../models/reportModel.js";

/**
 * Saves a detailed interview report to MongoDB with robust logging and error handling.
 */
export const saveReport = async (req, res) => {
  try {
    console.log("📥 Incoming Report Data Received...");
    console.log("--------------------------------------------------");
    console.log(JSON.stringify(req.body, null, 2));
    console.log("--------------------------------------------------");

    // Validate minimal requirements before persistence attempt
    if (!req.body.session_id || !req.body.user_id) {
        console.error("❌ Validation Failed: Missing session_id or user_id");
        return res.status(400).json({ 
            success: false, 
            message: "Missing mandatory session_id or user_id" 
        });
    }

    const report = await Report.create(req.body);

    console.log("✅ Report successfully saved to MongoDB Atlas");
    console.log("   Report ID:", report._id);

    res.status(201).json({
      success: true,
      data: report
    });

  } catch (error) {
    console.error("❌ MongoDB Save Pipeline Error:", error);

    res.status(500).json({
      success: false,
      message: error.message,
      detail: "Check if the payload matches the Mongoose schema exactly."
    });
  }
};
