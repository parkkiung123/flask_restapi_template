from marshmallow import Schema, fields, validate
from app.models.models import SensorType, SensorStatus

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    userid = fields.Str(required=True)
    userpass = fields.Str(required=True)

class LoginSchema(Schema):
    userid = fields.Str(required=True)
    userpass = fields.Str(required=True)

class SensorSchema(Schema):
    """Sensor テーブルのデータ構造を示すスキーマ。"""

    id = fields.Int(dump_only=True, description="入力順番を示す固有キー")
    device_id = fields.Str(
        required=True,
        validate=validate.Length(max=50),
        description="デバイスの識別ID（例: 'raspi-001'）"
    )
    type = fields.Str(
        required=True,
        validate=validate.OneOf([e.value for e in SensorType]),
        description=f"センサータイプ（{",".join([e.value for e in SensorType])}）"
    )
    data = fields.Dict(
        required=False,
        allow_none=True,
        description="センサーからの測定データ（JSON形式, keyはvalue, unit, latitude, longitude）"
    )
    timestamp = fields.DateTime(
        required=True,
        description="測定された日時"
    )
    status = fields.Int(
        required=True,
        validate=validate.OneOf([e.value for e in SensorStatus]),
        description="センサー状態（0 = OFF, 1 = ON）"
    )
    created_at = fields.DateTime(
        dump_only=True,
        description="レコード作成日時（自動入力）"
    )
    updated_at = fields.DateTime(
        dump_only=True,
        description="レコード最終更新日時（自動更新）"
    )

    class Meta:
        title = "Sensor"
        description = "センサー情報（デバイスID、センサータイプ、状態など）を管理するエンティティ。"