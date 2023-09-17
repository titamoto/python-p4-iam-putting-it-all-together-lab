#!/usr/bin/env python3

from flask import request, session, make_response, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        json = request.get_json()
        if 'username' not in json:
            return make_response({}, 422)
        user = User(
            username=json['username'],
            image_url=json['image_url'],
            bio=json['bio']
        )
        user.password_hash = json['password']
        db.session.add(user)
        db.session.commit()
        user_record = User.query.filter(User.username == user.username).first()
        if not user_record:
            return make_response({}, 422)
        session['user_id'] = user_record.id
        return make_response({
            "id": user_record.id,
            "username": user_record.username,
            "image URL": user_record.image_url,
            "bio": user_record.bio
        }, 201)

class CheckSession(Resource):
    def get(self):
        if session['user_id']:
            user_record = User.query.filter(User.id == session['user_id']).first()
            if not user_record:
                return make_response({}, 422)
            return make_response({
            "id": user_record.id,
            "username": user_record.username,
            "image URL": user_record.image_url,
            "bio": user_record.bio
        }, 200)
        return make_response({}, 401)

class Login(Resource):
    def post(self):
        json = request.get_json()
        if 'username' not in json:
            return make_response({}, 401)
        username = json['username']
        password = json['password']
        user = User.query.filter(User.username == username).first()
        if not user:
            return make_response({}, 401)
        if user.authenticate(password):
            session['user_id'] = user.id
            return make_response({
            "id": user.id,
            "username": user.username,
            "image URL": user.image_url,
            "bio": user.bio
        }, 200)
        return make_response({}, 401)

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session['user_id'] = None
            return make_response({'message': '204: No Content'}, 204)
        session['user_id'] = None
        return make_response({}, 401)

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            recipe_list = []
            for recipe in user.recipes:
                recipe_dict = {
                "title": recipe.title,
                "instructions": recipe.instructions,
                "minutes_to_complete": recipe.minutes_to_complete,
                }
                recipe_list.append(recipe_dict)
            return make_response(
                jsonify(recipe_list),
                200
            )

            # recipes = [recipe.to_dict() for recipe in Recipe.query.filter(Recipe.user_id == user_id).all()]
            # return make_response(jsonify(recipes), 200)
        return make_response({}, 401)
    
    def post(self):
        if not session.get('user_id'):
            return make_response({}, 401)
        recipe_form = request.get_json()
        if 'title' not in recipe_form:
            return make_response({}, 422)
        if 'instructions' not in recipe_form:
            return make_response({}, 422)
        if len(recipe_form['instructions']) < 50:
            return make_response({}, 422)            
        recipe = Recipe(
            title = recipe_form['title'],
            instructions = recipe_form['instructions'],
            minutes_to_complete = recipe_form['minutes_to_complete']
        )
        recipe.user_id = session['user_id']
        db.session.add(recipe)
        db.session.commit()

        recipe_record = Recipe.query.filter(Recipe.user_id == session['user_id']).filter(Recipe.title == recipe.title).first()
        if not recipe_record:
            return make_response({}, 422)
        user_record = User.query.filter(User.id == session['user_id']).first()
        return make_response(
            {
                "title": recipe_record.title,
                "instructions": recipe_record.instructions,
                "minutes_to_complete": recipe_record.minutes_to_complete,
                "user": {
            "id": user_record.id,
            "username": user_record.username,
            "image URL": user_record.image_url,
            "bio": user_record.bio
                }
            },
            201
        )


api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)
