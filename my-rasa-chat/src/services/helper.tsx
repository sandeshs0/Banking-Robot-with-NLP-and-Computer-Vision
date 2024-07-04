import axios from 'axios';

const BASE_URL = 'http://localhost:5005/webhooks/rest';
const myAxios = axios.create({
    baseURL: BASE_URL,
});

export const postMessage = async (message: string) => {
    const payload = {
        sender: 'user',
        message: message
    };

    try {
        const response = await myAxios.post('/webhook', payload);
        return response.data;
    } catch (error) {
        console.error('Error posting message:', error);
        throw error;
    }
};
