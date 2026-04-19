import mongoose from "mongoose";

const questionSchema = new mongoose.Schema({
  question: String,
  source: String,     // 'resume' | 'rag'
  answer: String,     // Flattened from userAnswer
  score: Number,
  feedback: {
    strengths: [String],
    weaknesses: [String]
  }
});

const skillSchema = new mongoose.Schema({
  dsa: Number,
  communication: Number,
  problem_solving: Number,
  system_design: Number,
  core_cs: Number
});

const reportSchema = new mongoose.Schema({
  session_id: {
    type: String,
    required: true,
    unique: false  // Changed to false for better resilience in dev retries
  },

  user_id: {
    type: String,
    required: true
  },

  company: String,
  role: String,
  interview_type: String,

  total_score: Number,
  breakdown: {
    resume_based: Number,
    company_based: Number
  },

  strengths: [String],
  weaknesses: [String],

  questions: [questionSchema],

  resume_summary: {
    skills: [String],
    projects: [String],
    experience: String
  },

  metadata: {
    total_questions: Number,
    duration_seconds: Number,
    difficulty_level: String,
    started_at: Date,
    completed_at: Date
  },

  createdAt: {
    type: Date,
    default: Date.now
  }
});

export default mongoose.model("Report", reportSchema);
