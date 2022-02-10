"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import requests
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Favorites


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.environ.get('FLASK_APP_KEY')
jwt = JWTManager(app)
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

url_base="https://www.swapi.tech/api/"

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/register', methods=['POST'])
def handle_register_user():
    body = request.json
    new_user = User.create(body)
    if new_user is not None:
        return jsonify(new_user.serialize()), 201
    else:
        return jsonify({"message": "User not created"}), 500


@app.route('/signin', methods=['POST'])
def handle_signin_user():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    name = request.json.get("name", None)
    user = User.query.filter_by(email= email, password= password, name=name).one_or_none()
    if user is not None:
        token = create_access_token(identity= user.id)
        return jsonify({"token": token, "user_id": user.id, "name": user.name}), 200
    else:
        return jsonify({"message": "Enter your credentials again"}), 401


#[GET] /people Get a list of all the people in the database
@app.route('/people', methods=['GET'])
def handle_all_people():
    response = requests.get(f"{url_base}/people?page=1&limit=1000")
    response = response.json()
    return jsonify(response), 200

#[GET] /people/<int:people_id> Get a one single people information
@app.route('/people/<int:id>', methods=['GET'])
def handle_id_people(id):
    response = requests.get(f"{url_base}/people/{id}")
    response = response.json()
    return jsonify(response) , 200

#[GET] /planets Get a list of all the planets in the database
@app.route('/planets', methods=['GET'])
def handle_all_planets():
    response = requests.get(f"{url_base}/planets?page=1&limit=1000")
    response = response.json()
    return jsonify(response), 200


#[GET] /planets/<int:planet_id>
@app.route('/planets/<int:id>', methods=['GET'])
def handle_id_planets(id):
    response = requests.get(f"{url_base}/planets/{id}")
    response = response.json()
    return jsonify(response) , 200


#[GET] /users Get a list of all the blog post users
@app.route('/users', methods=['GET'])
def handle_allusers():
    all_users = User.query.all()
    all_serialize = []
    for user in all_users:
        all_serialize.append(user.serialize())
    response_body = {
        'status': 'ok',
        'results': all_serialize
    }
    return (response_body) , 200
    
#[GET] /users/favorites Get all the favorites that belong to the current user.
@app.route('/favorites', methods=['GET'])
@jwt_required()
def handle_favorites_all():
    user_id= get_jwt_identity()
    favorites= Favorites.query.filter_by(user_id= user_id)
    response = []
    for favorite in favorites:
        response.append(favorite.serialize())
    return jsonify(response), 200

#[POST] /favorite/planet/<int:planet_id> Add a new favorite planet to the current user with the planet id = planet_id.
#[POST] /favorite/people/<int:planet_id> Add a new favorite people to the current user with the people id = people_id.
@app.route('/favorites/<string:type>', methods=['POST'])
@jwt_required()
def handle_add_favorite_by_type(type):
    uid = request.json["uid"]
    name = request.json["name"]
    favorite = Favorites(user_id = get_jwt_identity(), name = name, url = f"{url_base}/{type}/{uid}")
    db.session.add(favorite)
    try:
        db.session.commit()
        return jsonify(favorite.serialize()), 201
    except Exception as error:
        db.session.rollback()
        return jsonify(error), 500

#[DELETE] /favorite/planet/<int:planet_id> Delete favorite planet with the id = planet_id.
#[DELETE] /favorite/people/<int:people_id> Delete favorite people with the id = people_id.
@app.route('/favorites/<int:fav_id>', methods=['DELETE'])
def handle_fav_delete(fav_id):
    favorite = Favorites.query.filter_by(id= fav_id).one_or_none()
    if favorite is not None:
        favorite_delete = favorite.delete()
        if favorite_delete == True:
            return jsonify({"message": "Favorite deleted"}), 201
        else:
            return jsonify({"message":"Favorite not deleted"}), 500
    else:
        return jsonify({"message":"Favorite not found"}), 404

        
# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
