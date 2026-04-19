import app from './app.js';
import dotenv from 'dotenv';
import mongoose from 'mongoose';

dotenv.config();

const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017/nexus_mock_db";

mongoose.connect(MONGO_URI, {
    serverSelectionTimeoutMS: 10000 // Timeout after 10s to prevent hang
})
  .then(() => console.log('✅ Connected to MongoDB Analytics storage'))
  .catch((err) => {
    console.error('❌ MongoDB Connection Error');
    console.error('👉 TIP: If using Atlas, ensure your current IP is whitelisted (https://www.mongodb.com/docs/atlas/security-whitelist/)');
    console.error('👉 Falling back: Attempting to use local MongoDB if available...');
  });

app.listen(PORT, () => {
  console.log(`🚀 API Gateway running on port ${PORT}`);
});
