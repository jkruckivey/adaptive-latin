import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import { LearnerContext } from './App'; // Assuming App.js is now the context provider
import { useState } from 'react';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" />;
};

function App() {
    const [learnerId, setLearnerId] = useState(localStorage.getItem('learnerId'));
    const [learnerName, setLearnerName] = useState('');
    const [progress, setProgress] = useState(null);

  return (
    <LearnerContext.Provider value={{ learnerId, learnerName, progress, setLearnerId, setLearnerName, setProgress }}>
        <Router>
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route
            path="/dashboard"
            element={
                <PrivateRoute>
                <Dashboard />
                </PrivateRoute>
            }
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
        </Router>
    </LearnerContext.Provider>
  );
}

export default App;
