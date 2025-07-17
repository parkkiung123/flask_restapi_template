from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    userid = fields.Str(required=True)
    userpass = fields.Str(required=True)

class LoginSchema(Schema):
    userid = fields.Str(required=True)
    userpass = fields.Str(required=True)
