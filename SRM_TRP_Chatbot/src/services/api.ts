import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

export const sendMessage = async (message: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/chat`, { message });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

// Add more API calls as needed