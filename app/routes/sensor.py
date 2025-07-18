from flask.views import MethodView
from flask_smorest import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import Sensor, db, SensorType, SensorStatus
from app.schemas.schemas import SensorSchema

bp = Blueprint("sensor", __name__, description="センサーAPI")

@bp.route("/list")
class SensorList(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self):
        # 全センサー一覧を返す
        sensors = Sensor.query.all()
        return sensors
    
@bp.route("/getAll/<string:device_id>")
class SensorGetAllDataByDevice(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id):
        sensors = Sensor.query.filter_by(device_id=device_id).all()
        return sensors
    
@bp.route("/get/<string:device_id>/<int:dataNum>")
class SensorGetDataByDevice(MethodView):
    @bp.response(200, SensorSchema(many=True))
    def get(self, device_id, dataNum):
        # 降順で最新データを dataNum 件取得（効率重視）
        latest_data = (
            Sensor.query
            .filter_by(device_id=device_id)
            .order_by(Sensor.id.desc())
            .limit(dataNum)
            .all()
        )
        # 昇順にして返却
        return sorted(latest_data, key=lambda x: x.id)

@bp.route("/add")
class SensorAdd(MethodView):
    @bp.arguments(SensorSchema)
    @bp.response(201, SensorSchema)
    def post(self, data):
        sensor = Sensor(
            device_id=data["device_id"],
            type=SensorType(data["type"]),
            data=data.get("data"),
            timestamp=data["timestamp"],
            status=SensorStatus(data["status"]),
        )
        db.session.add(sensor)
        db.session.commit()
        return sensor
