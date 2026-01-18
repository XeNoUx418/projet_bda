// assets/js/config.js

// 1. Detect if we are in production (Render) or local development
const isProduction = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';

// 2. Set the root URL (Do NOT include '/api' here, api.js adds it)
//    Local: http://localhost:5000
//    Prod:  https://projet-bda-api.onrender.com
export const API_URL = isProduction 
    ? 'https://projet-bda-api.onrender.com' 
    : 'http://localhost:5000';
