import express from 'express';
import multer from 'multer';
import FormData from 'form-data';
import axios from 'axios';

const router = express.Router();
const upload = multer();

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    const formData = new FormData();
    formData.append("file", req.file.buffer, req.file.originalname);

    const response = await axios.post(
      "http://localhost:8000/api/resume/upload",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );

    res.json(response.data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Resume upload failed" });
  }
});

export default router;
