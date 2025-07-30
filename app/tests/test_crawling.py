import pytest
from unittest.mock import patch
from app.models.models import City

service_name = "crawling"

@pytest.fixture
def mock_city_data():
    """Cityテーブルのモックデータを作成"""
    city_data = [
        {"city": "Seoul", "coordinates": {"latitude": 37.5665, "longitude": 126.9783}, "temperature_url": "https://mockurl.com/seoul"},
        {"city": "Tokyo", "coordinates": {"latitude": 35.6762, "longitude": 139.6503}, "temperature_url": "https://mockurl.com/tokyo"},
    ]
    return city_data


@pytest.fixture
def seed_city_data(mock_city_data):
    """Cityテーブルにモックデータを挿入"""
    from app.extensions import db
    for data in mock_city_data:
        city = City(
            city=data["city"],
            coordinates=data["coordinates"],
            temperature_url=data["temperature_url"]
        )
        db.session.add(city)
    db.session.commit()
    yield
    db.session.remove()  # テスト終了後、DBセッションをリセット


def mock_get_temperature_by_url(url):
    """get_temperature_by_url関数のモック"""
    if "seoul" in url:
        return "27°C"
    elif "tokyo" in url:
        return "22°C"
    return None


# テストケース
def test_weather(client, api_prefix, seed_city_data):
    """/weather/<city> エンドポイントのテスト"""
    # モックを使ってget_temperature_by_urlをテスト
    with patch('app.routes.crawling.get_temperature_by_url', side_effect=mock_get_temperature_by_url):
        url = f"{api_prefix}/{service_name}/weather"
        response = client.get(url + "/seoul")
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["city"] == "Seoul"
        assert json_data["temperature"] == "27°C"

        # Tokyoも同様にテスト
        response = client.get(url + "/tokyo")
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["city"] == "Tokyo"
        assert json_data["temperature"] == "22°C"


def test_weather_all(client, api_prefix, seed_city_data):
    """/weatherAll エンドポイントのテスト"""
    with patch('app.routes.crawling.get_temperature_by_url', side_effect=mock_get_temperature_by_url):
        url = f"{api_prefix}/{service_name}/"
        response = client.get(url + "weatherAll")
        assert response.status_code == 200
        json_data = response.get_json()

        # 複数都市の天気情報が正しく返ってきていることを確認
        assert len(json_data) == 2
        cities = [data["city"] for data in json_data]
        assert "Seoul" in cities
        assert "Tokyo" in cities

        # Seoulの温度が27°C、Tokyoの温度が22°Cであることを確認
        seoul_data = next(item for item in json_data if item["city"] == "Seoul")
        tokyo_data = next(item for item in json_data if item["city"] == "Tokyo")
        assert seoul_data["temperature"] == "27°C"
        assert tokyo_data["temperature"] == "22°C"

def test_lotto10_real(client, api_prefix):
    """実際のデータを使用した /lotto10 エンドポイントのテスト"""
    url = f"{api_prefix}/{service_name}/lotto10"
    response = client.get(url)

    # 通信成功しているか確認
    assert response.status_code == 200

    json_data = response.get_json()
    
    # 結果がリストであること
    assert isinstance(json_data, list)

    # 要素数は10個
    assert len(json_data) == 10

    for entry in json_data:
        # 各要素は {回数: [番号...]} 形式
        assert isinstance(entry, dict)
        for draw_num_str, numbers in entry.items():
            try:
                draw_num = int(draw_num_str)
            except Exception:
                assert False, f"draw_numをintに変換できませんでした: {draw_num_str}"
            assert isinstance(draw_num, int)
            assert isinstance(numbers, list)
            assert len(numbers) == 7  # 通常は6つ＋ボーナス1つ
            for num in numbers:
                assert isinstance(num, int)
