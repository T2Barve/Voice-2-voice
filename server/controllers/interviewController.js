import { callFastAPI } from '../services/fastapiService.js';

export const startDSAInterview = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/dsa/start', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};

export const submitDSAAnswer = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/dsa/submit', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};

export const startTechnicalInterview = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/technical/start', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};

export const submitTechnicalAnswer = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/technical/submit', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};

export const startCaseStudyInterview = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/case-study/start', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};

export const submitCaseStudyAnswer = async (req, res, next) => {
  try {
    const data = await callFastAPI('/api/case-study/submit', req.body);
    res.json(data);
  } catch (err) {
    next(err);
  }
};
