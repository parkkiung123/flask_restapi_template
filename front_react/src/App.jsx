import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginForm from './components/LoginForm';
import RegisterForm from './components/RegisterForm';
import UserPage from './components/UserPage';
import { Container, CssBaseline } from '@mui/material';

function App() {
  return (
    <Router>
      <CssBaseline />
      <Container maxWidth="sm">
        <Routes>
          <Route path="/" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />
          <Route path="/users" element={<UserPage />} /> {/* ← JWT保護ページ */}
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
