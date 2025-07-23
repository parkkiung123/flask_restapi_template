import { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Stack,
  Alert,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function LoginForm() {
  const [userid, setUserid] = useState('');
  const [userpass, setUserpass] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);

    try {
      const response = await fetch('http://localhost:5000/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ userid, userpass }),
      });

      if (!response.ok) {
        throw new Error('ログインに失敗しました');
      }

      const data = await response.json();
      const { access_token } = data;

      // JWT トークンを保存
      localStorage.setItem('access_token', access_token);

      // ホーム画面に遷移
      navigate('/users');
    } catch (err) {
      console.error(err);
      setError('ログインに失敗しました。ユーザーIDまたはパスワードが間違っています。');
    }
  };

  const handleRegister = () => {
    navigate('/register');
  };

  return (
    <Paper elevation={3} sx={{ padding: 4, marginTop: 8 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        ログイン
      </Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <TextField
          margin="normal"
          required
          fullWidth
          label="ユーザーID"
          type="text"
          value={userid}
          onChange={(e) => setUserid(e.target.value)}
        />
        <TextField
          margin="normal"
          required
          fullWidth
          label="パスワード"
          type="password"
          value={userpass}
          onChange={(e) => setUserpass(e.target.value)}
        />
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
          <Button type="submit" variant="contained" fullWidth>
            ログイン
          </Button>
          <Button variant="outlined" fullWidth onClick={handleRegister}>
            ユーザー登録
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}
