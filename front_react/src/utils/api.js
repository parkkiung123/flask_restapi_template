const BASE_URL = "http://localhost:5000/api/v1";

export const API = {
  userList: `${BASE_URL}/user/list`,
  userAdd: `${BASE_URL}/user/add`,
  userDelete: `${BASE_URL}/user/delete`,
  userUpdate: `${BASE_URL}/user/update`,
  login: `${BASE_URL}/auth/login`,
  // 他のAPIエンドポイントもここに追加
};
