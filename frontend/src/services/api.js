import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 创建旅行计划
 */
export const createTravelPlan = async (preferences) => {
  const response = await api.post('/travel/plan', {
    preferences,
  });
  return response.data;
};

/**
 * 创建旅行计划（流式）
 */
export const createTravelPlanStream = async (preferences, onUpdate) => {
  const response = await fetch(`${API_BASE_URL}/travel/plan/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ preferences }),
  });

  if (!response.ok) {
    throw new Error('Failed to create travel plan');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') {
          return;
        }
        try {
          const event = JSON.parse(data);
          onUpdate(event);
        } catch (e) {
          console.error('Failed to parse event:', e);
        }
      }
    }
  }
};

export default api;
