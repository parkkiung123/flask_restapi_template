import { useEffect, useState } from "react";
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
} from "@mui/material";
import { useNavigate, useParams } from 'react-router-dom';
import { API } from '../utils/api';

export default function UpdateForm() {
  const { userId } = useParams();  // URLパラメータからユーザーIDを取得
  const [userid, setUserid] = useState("");
  const [name, setName] = useState("");
  const [userpass, setUserpass] = useState("");
  const [facephoto, setFacephoto] = useState(null);
  const navigate = useNavigate();

  // ユーザー情報の取得（初期値設定）
  useEffect(() => {
    const fetchUserData = async () => {
        const token = sessionStorage.getItem('access_token');
        
        if (!token) {
            setError('ログインセッションが無効です。');
            return;
        }

        try {
            const response = await fetch(`${API.userUpdate}/${userId}`, {
                method: 'GET',
                headers: {
                    Authorization: `Bearer ${token}`,  // トークンをヘッダーに追加
                },
            });

            if (!response.ok) {
            throw new Error('ユーザー情報の取得に失敗しました');
            }

            const data = await response.json();
            setUserid(data.userid);
            setName(data.name);
            setFacephoto(data.facephoto ? data.facephoto : null);
        } catch (error) {
            console.error(error);
            alert("ユーザー情報の取得に失敗しました");
        }
    };

    fetchUserData();
  }, [userId]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("userid", userid);
    formData.append("name", name);
    if (userpass) {
      formData.append("userpass", userpass);
    }
    if (facephoto) {
      formData.append("facephoto", facephoto);
    }

    try {
        const token = sessionStorage.getItem('access_token');
        
        if (!token) {
            setError('ログインセッションが無効です。');
            return;
        }
        const response = await fetch(`${API.userUpdate}/${userId}`, {
            method: "PUT",
            body: formData, // multipart/form-data自動設定
            headers: {
                Authorization: `Bearer ${token}`,  // トークンをヘッダーに追加
            },
        });

        if (!response.ok) {
            throw new Error("更新に失敗しました");
        }

        const data = await response.json();
        console.log("更新成功:", data);
        // 更新成功後の処理（例: ユーザー一覧ページに遷移）
        navigate("/users");
    } catch (error) {
      console.error(error);
      alert("更新に失敗しました");
    }
  };

  return (
    <Paper elevation={3} sx={{ padding: 4, marginTop: 8 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        ユーザー情報更新
      </Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <TextField
          label="ユーザーID"
          value={userid}
          onChange={(e) => setUserid(e.target.value)}
          fullWidth
          required
          margin="normal"
          disabled  // ユーザーIDは変更不可
        />
        <TextField
          label="名前"
          value={name}
          onChange={(e) => setName(e.target.value)}
          fullWidth
          required
          margin="normal"
        />
        <TextField
          label="新しいパスワード"
          type="password"
          value={userpass}
          onChange={(e) => setUserpass(e.target.value)}
          fullWidth
          margin="normal"
        />
        <Button
          variant="contained"
          component="label"
          sx={{ mt: 2, mb: 1 }}
        >
          顔写真を選択
          <input
            type="file"
            hidden
            accept="image/*"
            onChange={(e) => {
              setFacephoto(e.target.files[0]);
            }}
          />
        </Button>
        {facephoto && (
          <Typography variant="body2">{facephoto.name}</Typography>
        )}
        <Button
          type="submit"
          fullWidth
          variant="contained"
          sx={{ mt: 3 }}
        >
          更新
        </Button>
      </Box>
    </Paper>
  );
}
