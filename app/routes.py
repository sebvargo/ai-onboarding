# app/routes.py
from app import db
from app.models import User
from flask import Blueprint, request, jsonify, current_app
import openai
import os

# Load OpenAI API key
openai.api_key = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL_NAME = os.environ.get('OPENAI_MODEL_NAME')

api = Blueprint('api', __name__)

# USER ROUTES


@api.route('/api/user/<uuid:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return error_response("User not found", status_code=404)

    return success_response(user.to_dict())

@api.route('/api/user', methods=['GET'])
def get_users():
    users = db.session.query(User).all()
    return success_response([user.to_dict() for user in users])

@api.route('/api/user', methods=['POST'])
def create_user():
    data = request.json
    # Create a new user object
    user = User(**data)

    # Save the user to the database
    try:
        db.session.add(user)
        db.session.commit()
        return success_response({"user_uid": user.uid})
    except Exception as e:
        db.session.rollback()
        return error_response("Failed to create user", data={"error": str(e)})


# CONVERSATION ROUTES
# Route to handle onboarding conversation
@api.route('/api/onboarding', methods=['POST'])
def onboarding():
    data = request.json
    user_input = data.get('input')
    user_id = data.get('user_id')

    # Retrieve or create user object
    user = db.session.get(User, user_id)
    if not user:
        user = User(uid=user_id)
        db.session.add(user)
        db.session.commit()

    # A basic conversational flow
    if not user.name:
        if user_input:
            user.name = user_input
            db.session.commit()
            # Proceed to next question
            assistant_prompt = f"Great to meet you, {user.name}! What's your job title?"
        else:
            assistant_prompt = "Welcome! What's your name?"
    elif not user.title:
        if user_input:
            user.title = user_input
            db.session.commit()
            assistant_prompt = "What's the size of your company?"
        else:
            assistant_prompt = "What's your job title?"
    elif not user.company_size:
        if user_input:
            user.company_size = user_input
            db.session.commit()
            assistant_prompt = "How did you hear about us?"
        else:
            assistant_prompt = "What's the size of your company?"
    elif not user.heard_about_us:
        if user_input:
            user.heard_about_us = user_input
            db.session.commit()
            assistant_prompt = "Thank you for sharing! You're all set."
        else:
            assistant_prompt = "How did you hear about us?"
    else:
        assistant_prompt = "Onboarding complete."

    # Use OpenAI ChatCompletion
    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL_NAME,  # or "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a friendly onboarding assistant."},
            {"role": "user", "content": user_input or ""},
            {"role": "assistant", "content": assistant_prompt}
        ]
    )
    assistant_reply = response['choices'][0]['message']['content'].strip()
    return success_response({"response": assistant_reply, "user_id": user.uid})

# UTILS
def success_response(data: dict = {}, status_code: int = 200):
    return jsonify({"success": True, "data": data, "status_code":status_code})

def error_response(message: str = "", data: dict = {}, status_code: int = 400):
    return jsonify({"success": False, "message": message, "status_code":status_code, "data": data})