from marshmallow import Schema, fields, validate
from app.models.models import SensorType

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    userid = fields.Str(required=True)
    name = fields.Str(required=True)
    userpass = fields.Str(required=True)
    facephoto = fields.Method("get_facephoto", dump_only=True)
    def get_facephoto(self, obj):
        if obj.facephoto:
            import base64
            return base64.b64encode(obj.facephoto).decode('utf-8')
        return None

class UserListResScheme(Schema):
    userid = fields.Str(required=True)
    name = fields.Str(required=True)
    facephoto = fields.Method("get_facephoto", dump_only=True)
    def get_facephoto(self, obj):
        if obj.facephoto:
            import base64
            return base64.b64encode(obj.facephoto).decode('utf-8')
        return None

class LoginSchema(Schema):
    userid = fields.Str(required=True)
    userpass = fields.Str(required=True)

class DataSchema(Schema):
    value = fields.Float()
    unit = fields.Str()
    latitude = fields.Float()
    longitude = fields.Float()

class FileSchema(Schema):
    file = fields.Raw(
        required=True,
        metadata={"description": "アップロードするファイル", "format": "binary"}
    )

class File2Schema(FileSchema):
    file2 = fields.Raw(
        required=True,
        metadata={"description": "2つ目のアップロードファイル", "format": "binary"}
    )

class WeatherSchema(Schema):
    city = fields.Str(required=True)  # 都市名    
    lat = fields.Float()  # 緯度
    lon = fields.Float()  # 経度
    temperature = fields.Str()  # 温度

class MangaDexSchema(Schema):
    chapterId = fields.Str(
        required=True,
        description=(
            "chapterIdの例:\n"
            "- 58d69744-662e-4dfc-8ab1-cf4ffe60428e (Dragon Ball GT)\n"
            "- 3c2380be-dfaf-4f32-bdd6-6a6c8ae1e6bd (GTO)\n"
            "- de0ea6bc-3e3a-44e0-b325-ab5254713a97 (Slam Dunk)"
        ),
        example="58d69744-662e-4dfc-8ab1-cf4ffe60428e"
    )
    
class YoutubeDownloaderSchema(Schema):
    url = fields.Str(
        required=True,
        example="https://www.youtube.com/shorts/Mf7lTe55LY4"
    )

class ImageBase64Schema(Schema):
    image = fields.String(
        required=True,
        metadata={"description": "base64エンコードされた画像文字列（ヘッダーなし）"}
    )

class SensorSchema(Schema):
    id = fields.Int(
        dump_only=True,
        metadata={"description": "入力順番を示す固有キー"}
    )

    device_id = fields.Str(
        required=True,
        validate=validate.Length(max=50),
        metadata={"description": "デバイスの識別ID（例: 'raspi-001'）"}
    )

    type = fields.Method(
        serialize='get_type_value',
        deserialize='load_type_value',
        required=True,
        metadata={"description": "センサータイプ（face_dist, temperature）"}
    )

    def get_type_value(self, obj):
        return obj.type.value if isinstance(obj.type, SensorType) else obj.type

    def load_type_value(self, value):
        return SensorType(value)

    data = fields.Nested(
        DataSchema,
        required=False,
        allow_none=True,
        metadata={
            "description": (
                "センサーからの測定データ（JSON形式）\n\n"
                "face_dist => {\n"
                '    "value": 100.02,\n'
                '    "unit": "cm",\n'
                '    "latitude": 35.6895,\n'
                '    "longitude": 139.6917\n'
                "}\n\n"
                "temperature => {\n"
                '    "value": 30.5,\n'
                '    "unit": "Celsius",\n'
                '    "latitude": 35.6895,\n'
                '    "longitude": 139.6917\n'
                "}"
            )
        }
    )

    timestamp = fields.DateTime(
        required=True,
        metadata={"description": "測定された日時"}
    )

    status = fields.Int(
        required=True,
        metadata={"description": "センサー状態（0 = OFF, 1 = ON）"}
    )

    created_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "レコード作成日時（自動入力）"}
    )

    updated_at = fields.DateTime(
        dump_only=True,
        metadata={"description": "レコード最終更新日時（自動更新）"}
    )

    class Meta:
        title = "Sensor"
        description = "センサー情報（デバイスID、センサータイプ、状態など）を管理するエンティティ。"
