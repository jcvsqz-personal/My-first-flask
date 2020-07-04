from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'game.db')
app.config['JWT_SECRET_KEY'] = 'super_secret' #to be changed

app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '46b73b52dc8861'
app.config['MAIL_PASSWORD'] = '3a5479fb02be02'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)

@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('db created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('db dropped')


@app.cli.command('db_seed')
def db_seed():
    rubick = Hero(
        name="rubick",
        attack_type="magic",
        ranged=1,
        damage=48.1
    )

    es = Hero(
        name="es",
        attack_type="magic",
        ranged=0,
        damage=52.1
    )

    db.session.add(rubick)
    db.session.add(es)

    test_user = User(
        name="Peralta",
        email="peralta@email.com",
        password="password"
        )

    db.session.add(test_user)
    db.session.commit()
    print('db seeded')

@app.route('/')
def index():
    return jsonify(
        message='Hola',
        wellpayed='BOBO'
        )


@app.route('/not_found')
def not_found():
    return jsonify(message='Not found 404'), 404

@app.route('/person')
def person():
    name = request.args.get('name')
    return jsonify(message='Hi ' + name)


@app.route('/add/<string:name>/<int:age>')
def addPerson(name: str, age: int):
    return jsonify(message='Hi ' + name + " You're " + str(age))


@app.route('/heroes', methods=['GET'])
def heroes():
    heroes_list = Hero.query.all()
    result = heroes_schema.dump(heroes_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='Email already taken'), 409
    else:
        name = request.form['name']
        password = request.form['password']
        user = User(name=name, email=email, password=password)

        db.session.add(user)
        db.session.commit()
        return jsonify(message='User created successfuly'), 201

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login Succeeded', access_token=access_token)
    else:
        return jsonify(message='Wrong email or password'), 401

@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Password is ' + user.password,
            sender="adminko@jcvsqz.com",
            recipients=[email]
        )
        mail.send(msg)
        return jsonify(message="Password sent to " + email)
    else:
        return jsonify(message="Email doesn't exist"), 401


@app.route('/hero_details/<int:id>', methods=['GET'])
def hero_details(id: int):
    hero = Hero.query.filter_by(id=id).first()
    if hero:
        result = hero_schema.dump(hero)
        return jsonify(result)
    else:
        return jsonify(message="planet doesnt exist"), 404
    
@app.route('/add/hero', methods=['POST'])
@jwt_required
def addHero():
    name = request.form['name']
    test = Hero.query.filter_by(name=name).first()
    if test:
        return jsonify(message="Hero already exist"), 409
    else:
        attack_type = request.form['attack_type']
        ranged = int(request.form['ranged'])
        damage = float(request.form['damage'])

        new_hero = Hero(
            name=name,
            attack_type=attack_type,
            ranged=ranged,
            damage=damage
        )

        db.session.add(new_hero)
        db.session.commit()
        return jsonify(message="Successfuly creted new hero"), 201 #Add new data


@app.route('/hero/edit', methods=['PUT'])
@jwt_required
def updateHero():
    id = int(request.form['id'])
    hero = Hero.query.filter_by(id=id).first()
    if hero:
        hero.name = request.form['name']
        hero.damage = request.form['damage']

        db.session.commit()
        return jsonify(message="Hero: " + hero.name + " has successfully updated"), 202 #success
    else:
        return jsonify(message="error updating"), 401 


@app.route('/hero/delete/<int:id>', methods=['DELETE'])
def heroDelete(id: int):
    hero = Hero.query.filter_by(id=id).first()
    if hero:
        db.session.delete(hero)
        db.session.commit()
        return jsonify(message="Successfully Deleted"), 202
    else:
        return jsonify(message="Delete fail"), 404


#DB models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

class Hero(db.Model):
    __tablename__ = 'heroes'    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    attack_type = Column(String)
    ranged = Column(Integer)
    damage = Column(Float)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id','name','email','password')

class HeroSchema(ma.Schema):
    class Meta:
        fields = ('id','name','attack_type','ranged','damage')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

hero_schema = HeroSchema()
heroes_schema = HeroSchema(many=True)

if __name__ == '__main__':
    app.run(debug=True)