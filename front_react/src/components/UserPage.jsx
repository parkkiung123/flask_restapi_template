import { useEffect, useState } from 'react';
import {
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Alert,
  Avatar,
  Box,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function UserPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/'); // トークンがなければログイン画面へ
      return;
    }

    fetch('http://localhost:5000/api/v1/user/list', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(errorText || 'ユーザー情報の取得に失敗しました');
        }
        return res.json();
      })
      .then((data) => {
        setUsers(data);
      })
      .catch((err) => {
        console.error(err);
        setError('ユーザー一覧の取得に失敗しました。トークンが無効か、期限切れです。');
      });
  }, [navigate]);

  return (
    <Paper sx={{ padding: 4, marginTop: 8 }}>
      <Typography variant="h5" gutterBottom>
        ユーザー一覧
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <List>
        {users.map((user, index) => (
          <ListItem key={user.userid} divider alignItems="flex-start">
            {/* 顔写真があればAvatarで表示 */}
            {user.facephoto ? (
              <Avatar
                alt={user.name}
                src={`data:image/jpeg;base64,${user.facephoto}`}
                sx={{ width: 56, height: 56, mr: 2 }}
                variant="rounded"
              />
            ) : (
              <Avatar sx={{ width: 56, height: 56, mr: 2 }}>
                {user.name[0]}
              </Avatar>
            )}
            <ListItemText
              primary={
                <Box>
                  <strong>#{index + 1} {user.name}</strong>
                </Box>
              }
              secondary={`ユーザーID: ${user.userid}`}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
