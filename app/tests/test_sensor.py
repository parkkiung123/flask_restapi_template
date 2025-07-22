import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models.models import Sensor, SensorType

@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def sample_sensor(app):
    sensor = Sensor(
        device_id="dev123",
        type=SensorType.temperature,
        data={"value": 25},
        timestamp=datetime.utcnow(),
        status=1,
    )
    db.session.add(sensor)
    db.session.commit()
    return sensor

def test_get_list(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/list"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert isinstance(json_data, list)
    assert any(s["id"] == sample_sensor.id for s in json_data)

def test_get_all_by_device(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/getAll/{sample_sensor.device_id}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["device_id"] == sample_sensor.device_id for s in json_data)
    assert len(json_data) >= 1

def test_get_data_by_device_with_dataNum(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    dataNum = 1
    url = f"{prefix}/sensor/get/{sample_sensor.device_id}/{dataNum}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert isinstance(json_data, list)
    # 最新データが入っているか確認
    assert any(s["id"] == sample_sensor.id for s in json_data)

def test_add_sensor(client, app):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/add"
    new_sensor_data = {
        "device_id": "test_device_001",
        "type": "temperature",
        "data": {"value": 30},
        "timestamp": datetime.utcnow().isoformat(),
        "status": 1,
    }
    res = client.post(url, json=new_sensor_data)
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["device_id"] == new_sensor_data["device_id"]
    assert json_data["type"] == new_sensor_data["type"]
    assert json_data["data"] == new_sensor_data["data"]
    assert json_data["status"] == new_sensor_data["status"]

def test_get_by_id(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/getById/{sample_sensor.id}"
    print(f"Request URL: {url}")
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["id"] == sample_sensor.id
    assert json_data["device_id"] == "dev123"

def test_get_by_id_not_found(client, app):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/getById/9999"
    res = client.get(url)
    assert res.status_code == 404

def test_update_sensor(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    update_data = {
        "device_id": "dev456",
        "type": "face_dist",
        "data": {"value": 50},
        "timestamp": datetime.utcnow().isoformat(),
        "status": 0
    }
    url = f"{prefix}/sensor/update/{sample_sensor.id}"
    res = client.put(url, json=update_data)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["device_id"] == "dev456"
    assert json_data["type"] == "face_dist"
    assert json_data["status"] == 0

def test_delete_sensor(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/delete/{sample_sensor.id}"
    res = client.delete(url)
    assert res.status_code == 204
    # 削除後に取得しようとすると404
    res2 = client.get(f"{prefix}/sensor/getById/{sample_sensor.id}")
    assert res2.status_code == 404

def test_get_by_date_range(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    start = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1)).isoformat()
    url = f"{prefix}/sensor/getByDateRange/{sample_sensor.device_id}?start={start}&end={end}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert len(json_data) >= 1
    assert json_data[0]["device_id"] == sample_sensor.device_id

def test_get_latest(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/getLatest/{sample_sensor.device_id}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["id"] == sample_sensor.id

def test_get_by_status(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    status = sample_sensor.status
    url = f"{prefix}/sensor/getByStatus/{sample_sensor.device_id}/{status}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["status"] == sample_sensor.status for s in json_data)

def test_get_by_type(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    sensor_type = sample_sensor.type.value
    url = f"{prefix}/sensor/getByType/{sample_sensor.device_id}/{sensor_type}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["type"] == sensor_type for s in json_data)

def test_get_by_type_invalid(client, app, sample_sensor):
    prefix = app.config["API_URL_PREFIX"]
    url = f"{prefix}/sensor/getByType/{sample_sensor.device_id}/invalid_type"
    res = client.get(url)
    assert res.status_code == 400
