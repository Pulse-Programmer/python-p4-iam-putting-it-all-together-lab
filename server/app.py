#!/usr/bin/env python3

from flask import request, session, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        bio = data.get('bio')
        image_url = data.get('image_url')

        if not username or not password:
            return {'message': 'username and password required'}, 400

        user = User(
            username=username,
            bio=bio,
            image_url=image_url
        )
        user.password_hash = password

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
        
        session['user_id'] = user.id
        
        response_body = user.to_dict(rules=('-_password_hash',))
        return response_body, 201    
            

class CheckSession(Resource):
    def get(self):
        if session.get('user_id'):
            user = User.query.filter(User.id == session['user_id']).first()
            response_body = user.to_dict(rules=('-_password_hash',))
            return response_body, 200
        else:
            return {'message': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'message': 'username and password required'}, 400

        user = User.query.filter(User.username == username).first()

        if user and user.authenticate(password):
            session['user_id'] = user.id
            response_body = user.to_dict(rules=('-_password_hash',))
            return response_body, 200
        else:
            return {'message': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'message': 'Unauthorized'}, 401
        session['user_id'] = None
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'message': 'Unauthorized'}, 401
        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200
    
    def post(self):
        if not session.get('user_id'):
            return {'message': 'Unauthorized'}, 401
        data = request.get_json()
        title = data.get('title')
        instructions = data.get('instructions')
        minutes_to_complete = data.get('minutes_to_complete')
        user_id = session['user_id']

        if not title or not instructions or not minutes_to_complete:
            return {'message': 'title, instructions, and minutes to complete required'}, 400
        try:
            recipe = Recipe(
                title=title,
                instructions=instructions,
                minutes_to_complete=minutes_to_complete,
                user_id=user_id
            )
        
            db.session.add(recipe)
            db.session.commit()
            

            response_body = recipe.to_dict()
            return response_body, 201
        except Exception as e:
            return make_response({'errors': [e.args]}, 422)
           
        

        

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)