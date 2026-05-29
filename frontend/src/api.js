import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,
});

export const checkAuth = async () => {
  try {
    const res = await api.get('/me');
    return res.data;
  } catch (err) {
    throw err;
  }
};

export const logout = async () => {
  await api.post('/auth/logout');
};

export const sendMessage = async (message, sessionId) => {
  const res = await api.post('/chat', {
    message,
    session_id: sessionId
  });
  return res.data;
};

export default api;
