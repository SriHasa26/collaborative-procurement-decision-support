import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/variables.css'
import './styles/global.css'
import './styles/layout.css'
import './styles/components.css'
import './styles/analysis.css'
import './styles/results.css'
import './styles/auth.css'
import './styles/landing.css'
import './styles/dashboard.css'
import './styles/history.css'
import './styles/insights.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
