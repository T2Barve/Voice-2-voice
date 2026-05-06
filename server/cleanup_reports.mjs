import mongoose from 'mongoose';
import dotenv from 'dotenv';
dotenv.config();

const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/nexus_mock_db';

async function cleanReports() {
  await mongoose.connect(MONGO_URI, { serverSelectionTimeoutMS: 10000 });
  console.log('Connected to MongoDB');

  const Report = mongoose.model('Report', new mongoose.Schema({}, { strict: false }), 'reports');

  const total = await Report.countDocuments();
  console.log(`Found ${total} reports in MongoDB`);

  const result = await Report.deleteMany({});
  console.log(`Deleted ${result.deletedCount} reports. Collection is now clean.`);

  await mongoose.disconnect();
  console.log('Done.');
}

cleanReports().catch(e => { console.error(e.message); process.exit(1); });
