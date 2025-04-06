from flask.views import MethodView
from flask_smorest import abort, Blueprint
from sqlalchemy.exc import SQLAlchemyError
from db import db
from models import AddressModel
from resources.schemas import AddressSchema, AddressUpdateSchema
import requests

blp = Blueprint("Addresses", __name__, description="Operations on addresses")


def fetch_address_from_viacep(zip_code):
    """Fetch address details from ViaCEP API with timeout handling."""
    try:
        response = requests.get(
            f"https://viacep.com.br/ws/{zip_code}/json/", timeout=30
        )
        response.raise_for_status()
        data = response.json()
        if "erro" not in data:
            return {
                "street": data.get("logradouro", ""),
                "district": data.get("bairro", ""),
                "city": data.get("localidade", ""),
                "state": data.get("uf", ""),
                "zip_code": zip_code,
                "country": "Brazil",
            }
    except requests.RequestException:
        abort(400, message="Could not fetch address from ViaCEP. Try again later.")
    return None


@blp.route("/address/<int:address_id>")
class Address(MethodView):
    @blp.response(200, AddressSchema)
    def get(self, address_id):
        """Retrieve an address by ID"""
        return AddressModel.query.get_or_404(address_id)

    def delete(self, address_id):
        """Delete an address by ID"""
        address = AddressModel.query.get_or_404(address_id)
        db.session.delete(address)
        db.session.commit()
        return {"message": "Address deleted successfully"}, 200

    @blp.arguments(AddressUpdateSchema)
    @blp.response(200, AddressSchema)
    def put(self, address_data, address_id):
        """Update an existing address"""
        address = AddressModel.query.get_or_404(address_id)

        new_zip_code = address_data.get("zip_code")

        if new_zip_code:
            fetched_address = fetch_address_from_viacep(new_zip_code)
            if not fetched_address:
                abort(400, message="Invalid zip code or ViaCEP service error")

            for key, value in fetched_address.items():
                setattr(address, key, value)

        for key, value in address_data.items():
            if key != "zip_code":
                setattr(address, key, value)

        db.session.commit()
        return address


@blp.route("/address")
class AddressList(MethodView):
    @blp.response(200, AddressSchema(many=True))
    def get(self):
        """Retrieve all addresses"""
        return AddressModel.query.all()

    @blp.arguments(AddressSchema)
    @blp.response(201, AddressSchema)
    def post(self, address_data):
        """Create a new address with auto-filled details from ViaCEP"""
        zip_code = address_data.get("zip_code")

        if not zip_code:
            abort(400, message="Zip code is required")

        fetched_address = fetch_address_from_viacep(zip_code)

        if not fetched_address:
            abort(400, message="Invalid zip code or ViaCEP service error")

        final_address_data = {**fetched_address, **address_data}

        address = AddressModel(**final_address_data)

        try:
            db.session.add(address)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Error inserting the address")

        return address, 201


@blp.route("/address/lookup/<string:zip_code>")
class AddressLookup(MethodView):
    @blp.response(200, AddressSchema)
    def get(self, zip_code):
        """Retrieve address details from ViaCEP API based on zip code"""
        fetched_address = fetch_address_from_viacep(zip_code)

        if not fetched_address:
            abort(400, message="Invalid zip code or ViaCEP service error")

        return fetched_address
