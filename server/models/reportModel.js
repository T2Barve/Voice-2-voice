import mongoose from "mongoose";

const questionSchema = new mongoose.Schema({
  question: String,
  source: String,     // 'resume' | 'rag'
  answer: String,
  score: Number,
  feedback: {
    strengths: [String],
    weaknesses: [String]
  }
});

const reportSchema = new mongoose.Schema({
  session_id: {
    type: String,
    required: true,
    unique: false
  },

  user_id: {
    type: String,
    required: true,
    index: true
  },

  company:        { type: String, default: 'Unknown' },
  role:           { type: String, default: 'SDE' },
  interview_type: { type: String, default: 'technical' },  // 'dsa' | 'technical' | 'case_study'

  // Unified score field — all workflows must send this
  score: { type: Number, default: 0 },

  breakdown: {
    resume_based:  { type: Number, default: 0 },
    company_based: { type: Number, default: 0 }
  },

  strengths:  [String],
  weaknesses: [String],

  questions: [questionSchema],

  resume_summary: {
    skills:     [String],
    projects:   [String],
    experience: String
  },

  metadata: {
    total_questions:  Number,
    duration_seconds: Number,
    difficulty_level: String,
    started_at:       Date,
    completed_at:     Date
  },

  createdAt: {
    type: Date,
    default: Date.now
  }
});

export default mongoose.model("Report", reportSchema);
