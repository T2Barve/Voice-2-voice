import express from 'express';
import multer from 'multer';
import FormData from 'form-data';
import axios from 'axios';

const router = express.Router();
const upload = multer();

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded. Please select a PDF.' });
    }

    const formData = new FormData();
    formData.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype || 'application/pdf',
    });

    const response = await axios.post(
      `${FASTAPI_URL}/api/resume/upload`,
      formData,
      { headers: formData.getHeaders() }  // includes correct multipart boundary
    );

    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const detail = err.response?.data?.detail || err.message || 'Resume upload failed';
    console.error('[ResumeRoute] Upload error:', detail);
    res.status(status).json({ error: detail });
  }
});

router.post('/analyze', async (req, res) => {
  try {
    const { resume_text } = req.body;
    const response = await axios.post(`${FASTAPI_URL}/api/resume/analyze`, { resume_text });
    res.json(response.data);
  } catch (err) {
    const status = err.response?.status || 500;
    const detail = err.response?.data?.detail || err.message || 'Resume analysis failed';
    res.status(status).json({ error: detail });
  }
});

export default router;
