import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

/**
 * Submit optimization request
 * @param {FormData} formData - Form data with CSV files and parameters
 * @returns {Promise<string>} Task ID
 */
export async function submitOptimization(formData) {
  const response = await apiClient.post('/api/optimize', formData);
  return response.data.task_id;
}

/**
 * Get optimization status
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Status object with progress, message, and results
 */
export async function getOptimizationStatus(taskId) {
  const response = await apiClient.get(`/api/status/${taskId}`);
  return response.data;
}

/**
 * Get optimization results
 * @param {string} taskId - Task ID
 * @returns {Promise<Object>} Results object
 */
export async function getOptimizationResults(taskId) {
  const response = await apiClient.get(`/api/results/${taskId}`);
  return response.data;
}

export default apiClient;
