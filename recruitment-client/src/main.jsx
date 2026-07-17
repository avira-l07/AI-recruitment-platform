import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import './styles/colors.css';
import './styles/variables.css';
import './styles/typography.css';
import './styles/spacing.css';
import './styles/animations.css';
import './styles/elevation.css';
import './index.css';
import { BrowserRouter } from 'react-router-dom';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
