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
  IconButton,
  Button,  // 追加：ログアウトボタン用
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { API } from '../utils/api';
import DeleteIcon from '@mui/icons-material/Delete';  // 削除アイコン
import EditIcon from '@mui/icons-material/Edit';    // 更新アイコン（追加）

export default function UserPage() {
  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      navigate('/'); // トークンがなければログイン画面へ
      return;
    }

    fetch(API.userList, {
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

  const handleDelete = (userId) => {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
      setError('ログインセッションが無効です。');
      return;
    }

    fetch(`${API.userDelete}/${userId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(errorText || 'ユーザー削除に失敗しました');
        }
        return res.json();
      })
      .then(() => {
        // 削除後、ユーザーリストを再取得して更新
        setUsers(users.filter(user => user.userid !== userId));
      })
      .catch((err) => {
        console.error(err);
        setError('ユーザー削除に失敗しました。');
      });
  };

  const handleLogout = () => {
    sessionStorage.removeItem('access_token'); // トークン削除
    navigate('/'); // ログイン画面にリダイレクト
  };

  const handleUpdate = (userId) => {
    navigate(`/update/${userId}`); // 更新ページに遷移
  };

  return (
    <Paper sx={{ padding: 4, marginTop: 8 }}>
      <Typography variant="h5" gutterBottom>
        ユーザー一覧
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Button 
        variant="outlined" 
        color="primary" 
        onClick={handleLogout} 
        sx={{ mb: 2 }}
      >
        ログアウト
      </Button>

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
            {/* 削除アイコン */}
            <IconButton
              edge="end"
              color="error"
              onClick={() => handleDelete(user.userid)}
              sx={{ ml: 2 }}
            >
              <DeleteIcon />
            </IconButton>
            {/* 更新アイコン */}
            <IconButton
              edge="end"
              color="primary"
              onClick={() => handleUpdate(user.userid)}  // 更新ページに遷移
              sx={{ ml: 2 }}
            >
              <EditIcon />
            </IconButton>
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
