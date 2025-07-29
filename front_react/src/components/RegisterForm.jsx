import { useState } from "react";
import {
  Paper,
  Typography,
  Box,
  TextField,
  Button,
} from "@mui/material";
import { useNavigate } from 'react-router-dom';
import { API } from '../utils/api';

export default function RegisterForm() {
  const [userid, setUserid] = useState("");
  const [name, setName] = useState("");
  const [userpass, setUserpass] = useState("");
  const [facephoto, setFacephoto] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData();
    formData.append("userid", userid);
    formData.append("name", name);
    formData.append("userpass", userpass);
    if (facephoto) {
      formData.append("facephoto", facephoto);
    }

    try {
      const response = await fetch(API.userAdd, {
        method: "POST",
        body: formData, // multipart/form-data自動設定
      });

      if (!response.ok) {
        throw new Error("登録に失敗しました");
      }

      const data = await response.json();
      console.log("登録成功:", data);
      // 登録成功後の処理（例: フォームリセットや遷移）
      navigate('/');
    } catch (error) {
      console.error(error);
      alert("登録に失敗しました");
    }
  };

  return (
    <Paper elevation={3} sx={{ padding: 4, marginTop: 8 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        ユーザー登録
      </Typography>
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <TextField
          label="ユーザーID"
          value={userid}
          onChange={(e) => setUserid(e.target.value)}
          fullWidth
          required
          margin="normal"
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
          label="パスワード"
          type="password"
          value={userpass}
          onChange={(e) => setUserpass(e.target.value)}
          fullWidth
          required
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
          登録
        </Button>
      </Box>
    </Paper>
  );
}
