from datetime import datetime, date
from flask import request, abort
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required
from sqlalchemy import and_
from app.models.models import Sensor, db, SensorType
from app.schemas.schemas import SensorSchema

bp = Blueprint("sensor", __name__, description="センサーAPI")

@bp.route("/list")
class SensorList(MethodView):
    @bp.doc(description="全センサーの一覧を取得します")  # ここでAPI説明を追加
    @bp.response(200, SensorSchema(many=True))
    def get(self):
        # 全センサー一覧を返す
        sensors = Sensor.query.all()
        return sensors
    
@bp.route("/getAll/<string:device_id>")
class SensorGetAllDataByDevice(MethodView):
    @bp.doc(
        description="指定したdevice_idの全センサー情報を取得します",
        parameters=[
            {
                "in": "path",
                "name": "device_id",
                "schema": {"type": "string"},
                "required": True,
                "description": "デバイスID"
            }
        ]            
    )
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id):
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        return sensors
    
@bp.route("/get/<string:device_id>/<int:dataNum>")
class SensorGetDataByDevice(MethodView):
    @bp.doc(
        description="指定device_idの本日の最新データをdataNum個取得します",
        parameters=[
            {
                "in": "path",
                "name": "device_id",
                "schema": {"type": "string"},
                "required": True,
                "description": "デバイスID"
            },
            {
                "in": "path",
                "name": "dataNum",
                "schema": {"type": "int"},
                "required": True,
                "description": "取得するデータの件数"
            }
        ]
    )
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id, dataNum):
        # 今日の0:00（UTCの場合、ローカルに合わせるなら tz-aware に調整）
        today_start = datetime.combine(date.today(), datetime.min.time())
        # 最新の今日のデータを dataNum 件取得（降順）
        latest_data = (
            Sensor.query
            .filter(
                and_(
                    Sensor.device_id == device_id,
                    Sensor.timestamp >= today_start
                )
            )
            .order_by(Sensor.id.desc())
            .limit(dataNum)
            .all()
        )
        # 昇順にして返却
        return sorted(latest_data, key=lambda x: x.id)

@bp.route("/add")
class SensorAdd(MethodView):
    @jwt_required()
    @bp.arguments(SensorSchema)
    @bp.response(201, SensorSchema)
    def post(self, data):
        """保護されたルート（JWT 必須）"""
        sensor = Sensor(
            device_id=data["device_id"],
            type=SensorType(data["type"]),
            data=data.get("data"),
            timestamp=data["timestamp"],
            status=int(data["status"]),
        )
        db.session.add(sensor)
        db.session.commit()
        return sensor

# --- /getById/<int:id> ---
@bp.route("/getById/<int:id>")
class SensorGetById(MethodView):
    @bp.response(200, SensorSchema)
    def get(self, id):
        sensor = db.session.get(Sensor, id)
        if not sensor:
            abort(404, description="Sensor not found")
        return sensor

# --- /update/<int:id> ---
@bp.route("/update/<int:id>")
class SensorUpdate(MethodView):
    @bp.arguments(SensorSchema)
    @bp.response(200, SensorSchema)
    def put(self, data, id):
        sensor = db.session.get(Sensor, id)
        if not sensor:
            abort(404, description="Sensor not found")

        sensor.device_id = data.get("device_id", sensor.device_id)
        sensor.type = SensorType(data["type"]) if "type" in data else sensor.type
        sensor.data = data.get("data", sensor.data)
        sensor.timestamp = data.get("timestamp", sensor.timestamp)
        sensor.status = int(data["status"])

        db.session.commit()
        return sensor

# --- /delete/<int:id> ---
@bp.route("/delete/<int:id>")
class SensorDelete(MethodView):
    @bp.response(204)
    def delete(self, id):
        sensor = db.session.get(Sensor, id)
        if not sensor:
            abort(404, description="Sensor not found")

        db.session.delete(sensor)
        db.session.commit()
        return "", 204

# --- /getByDateRange/<string:device_id> ---
@bp.route("/getByDateRange/<string:device_id>")
class SensorGetByDateRange(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id):
        start_date = request.args.get("start")
        end_date = request.args.get("end")

        if not start_date or not end_date:
            abort(400, description="start and end query parameters are required")

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            abort(400, description="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        sensors = (
            Sensor.query.filter(
                Sensor.device_id == device_id,
                Sensor.timestamp >= start_dt,
                Sensor.timestamp <= end_dt,
            )
            .order_by(Sensor.timestamp.asc())
            .all()
        )
        return sensors

# --- /getLatest/<string:device_id> ---
@bp.route("/getLatest/<string:device_id>")
class SensorGetLatest(MethodView):
    @bp.response(200, SensorSchema)
    def get(self, device_id):
        sensor = (
            Sensor.query.filter_by(device_id=device_id)
            .order_by(Sensor.timestamp.desc())
            .first()
        )
        if not sensor:
            abort(404, description="No sensor data found")
        return sensor

# --- /getByStatus/<string:device_id>/<int:status> ---
@bp.route("/getByStatus/<string:device_id>/<int:status>")
class SensorGetByStatus(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id, status):
        sensors = Sensor.query.filter_by(device_id=device_id, status=status).all()
        return sensors

# --- /getByType/<string:device_id>/<string:type> ---
@bp.route("/getByType/<string:device_id>/<string:type>")
class SensorGetByType(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id, type):
        try:
            type_enum = SensorType(type)
        except ValueError:
            abort(400, description="Invalid sensor type")

        sensors = Sensor.query.filter_by(device_id=device_id, type=type_enum).all()
        return sensors
