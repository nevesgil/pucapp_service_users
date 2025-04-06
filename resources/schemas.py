from marshmallow import Schema, fields


class PlainUserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    birthdate = fields.Date(required=True)


class PlainAddressSchema(Schema):
    id = fields.Int(dump_only=True)
    street = fields.Str(required=False)
    district = fields.Str(required=False)
    city = fields.Str(required=False)
    state = fields.Str(required=False)
    zip_code = fields.Str(required=True)
    country = fields.Str(required=False)


class UserSchema(PlainUserSchema):
    addresses = fields.List(fields.Nested(PlainAddressSchema(), dump_only=True))


class AddressSchema(PlainAddressSchema):
    user_id = fields.Int(load_only=True)
    user = fields.Nested(PlainUserSchema(), dump_only=True)


class UserUpdateSchema(Schema):
    name = fields.Str()
    birthdate = fields.Date()


class AddressUpdateSchema(Schema):
    street = fields.Str()
    district = fields.Str()
    city = fields.Str()
    state = fields.Str()
    zip_code = fields.Str()
    country = fields.Str()
