import axios from 'axios';

const BASE_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

export const callFastAPI = async (endpoint, data) => {
  try {
    const res = await axios.post(`${BASE_URL}${endpoint}`, data);
    return res.data;
  } catch (err) {
    if (err.response) {
      throw new Error(`FastAPI Error: ${err.response.data.detail || err.message}`);
    }
    throw new Error("FastAPI Connection Error: " + err.message);
  }
};

export const getFastAPI = async (endpoint) => {
  try {
    const res = await axios.get(`${BASE_URL}${endpoint}`);
    return res.data;
  } catch (err) {
    if (err.response) {
      throw new Error(`FastAPI Error: ${err.response.data.detail || err.message}`);
    }
    throw new Error("FastAPI Connection Error: " + err.message);
  }
};
