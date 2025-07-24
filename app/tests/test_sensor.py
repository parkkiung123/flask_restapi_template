import pytest
from datetime import datetime, timedelta
from app import db
from app.models.models import Sensor, SensorType

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

def test_get_list(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/list"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert isinstance(json_data, list)
    assert any(s["id"] == sample_sensor.id for s in json_data)

def test_get_all_by_device(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/getAll/{sample_sensor.device_id}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["device_id"] == sample_sensor.device_id for s in json_data)
    assert len(json_data) >= 1

def test_get_data_by_device_with_dataNum(client, api_prefix, sample_sensor):
    dataNum = 1
    url = f"{api_prefix}/sensor/get/{sample_sensor.device_id}/{dataNum}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert isinstance(json_data, list)
    # 最新データが入っているか確認
    assert any(s["id"] == sample_sensor.id for s in json_data)

def test_add_sensor(client, api_prefix, access_token):
    url = f"{api_prefix}/sensor/add"
    new_sensor_data = {
        "device_id": "test_device_001",
        "type": "temperature",
        "data": {"value": 30},
        "timestamp": datetime.utcnow().isoformat(),
        "status": 1,
    }
    res = client.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        json=new_sensor_data
    )
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["device_id"] == new_sensor_data["device_id"]
    assert json_data["type"] == new_sensor_data["type"]
    assert json_data["data"] == new_sensor_data["data"]
    assert json_data["status"] == new_sensor_data["status"]

def test_get_by_id(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/getById/{sample_sensor.id}"
    print(f"Request URL: {url}")
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["id"] == sample_sensor.id
    assert json_data["device_id"] == "dev123"

def test_get_by_id_not_found(client, api_prefix):
    url = f"{api_prefix}/sensor/getById/9999"
    res = client.get(url)
    assert res.status_code == 404

def test_update_sensor(client, api_prefix, sample_sensor):
    update_data = {
        "device_id": "dev456",
        "type": "face_dist",
        "data": {"value": 50},
        "timestamp": datetime.utcnow().isoformat(),
        "status": 0
    }
    url = f"{api_prefix}/sensor/update/{sample_sensor.id}"
    res = client.put(url, json=update_data)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["device_id"] == "dev456"
    assert json_data["type"] == "face_dist"
    assert json_data["status"] == 0

def test_delete_sensor(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/delete/{sample_sensor.id}"
    res = client.delete(url)
    assert res.status_code == 204
    # 削除後に取得しようとすると404
    res2 = client.get(f"{api_prefix}/sensor/getById/{sample_sensor.id}")
    assert res2.status_code == 404

def test_get_by_date_range(client, api_prefix, sample_sensor):
    start = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1)).isoformat()
    url = f"{api_prefix}/sensor/getByDateRange/{sample_sensor.device_id}?start={start}&end={end}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert len(json_data) >= 1
    assert json_data[0]["device_id"] == sample_sensor.device_id

def test_get_latest(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/getLatest/{sample_sensor.device_id}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["id"] == sample_sensor.id

def test_get_by_status(client, api_prefix, sample_sensor):
    status = sample_sensor.status
    url = f"{api_prefix}/sensor/getByStatus/{sample_sensor.device_id}/{status}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["status"] == sample_sensor.status for s in json_data)

def test_get_by_type(client, api_prefix, sample_sensor):
    sensor_type = sample_sensor.type.value
    url = f"{api_prefix}/sensor/getByType/{sample_sensor.device_id}/{sensor_type}"
    res = client.get(url)
    assert res.status_code == 200
    json_data = res.get_json()
    assert all(s["type"] == sensor_type for s in json_data)

def test_get_by_type_invalid(client, api_prefix, sample_sensor):
    url = f"{api_prefix}/sensor/getByType/{sample_sensor.device_id}/invalid_type"
    res = client.get(url)
    assert res.status_code == 400
