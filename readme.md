# 起動法
flask db init                   # 初期化（初回だけ）rm -r migrations (Error: Directory migrations already exists and is not empty)
flask db migrate -m "init"      # モデルからマイグレーションスクリプト作成
flask db upgrade                # テーブルをDBに反映
python seed.py
flask run

# ログイン
curl.exe -X POST http://localhost:5000/api/v1/auth/login -H "Content-Type: application/json" -d @test_data/user.json

# 保護ルート（トークン要）
curl.exe -H "Authorization: Bearer <トークン>" http://localhost:5000/api/v1/user/list
# エラー{"msg":"Missing Authorization Header"}
curl.exe http://localhost:5000/api/v1/user/list

# ユーザー追加
curl.exe -X POST http://localhost:5000/api/v1/user/add -H "Authorization: Bearer <トークン>" -H "Content-Type: application/json" -d @test_data/users_input.json
仕様変更
cmd
curl -X POST -d "userid=user1&name=name1&userpass=userpass1" http://localhost:5000/api/v1/user/add

✅ 対策①：use_reloader=False を明示する（開発時）
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
これで実行は 1回だけ になります。

# センサーリスト
curl.exe http://localhost:5000/api/v1/sensor/list

# センサー入力
curl.exe -X POST http://localhost:5000/api/v1/sensor/add -H "Content-Type: application/json" -d @test_data/sensors_input.json

# テスト
pytest -v
pytest app/tests/test_sensor.py
pytest app/tests/test_sensor.py::test_get_list

# grpcコードの作成 (画像処理用)
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image.proto

# grpcサーバーの起動
python -m app.grpc_server.server

# pythonのキャッシュ削除
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force

# 一時的にPowerShellを管理者として実行
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 仮想環境
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

# 参照
古典籍の画像の文字認識 https://github.com/ndl-lab/ndlkotenocr-lite

# swagger doc
localhost:5000/docs

# flask 起動
仮想環境インストール後
flask run

# 画像処理 grpcサーバーの起動
python -m app.grpc_server.server

# 全体テスト(chatGPT生成)
pytest -v