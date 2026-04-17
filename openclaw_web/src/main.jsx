import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

// StrictMode disabled: causes WebSocket to be created/destroyed twice in dev mode
createRoot(document.getElementById('root')).render(<App />)
