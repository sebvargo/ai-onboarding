# app/routes.py
from app import db
from app.models import User
from dataclasses import dataclass
from flask import Blueprint, request, jsonify, current_app
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Load OpenAI API key
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

@api.route('/api/user/<uuid:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    user = db.session.get(User, user_id)
    if not user:
        return error_response("User not found", status_code=404)

    for key, value in data.items():
        setattr(user, key, value)

    db.session.commit()
    return success_response(user.to_dict())

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


@api.route('/api/onboarding', methods=['POST'])
def onboarding():
    data = request.json
    user_input = data.get('input')
    user_id = data.get('user_id')

    # Retrieve or create user
    user = db.session.get(User, user_id)
    if not user:
        user = User(uid=user_id)
        db.session.add(user)
        db.session.commit()

    current_step = ONBOARDING_STEPS.get(user.onboarding_step)
    
    if not current_step:
        return success_response({
            "response": "Onboarding complete! Thank you for sharing your information.",
            "user_id": user.uid
        })

    if user_input:
        # Validate input with AI
        validation_response = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[
                {"role": "system", "content": current_step.validation_prompt},
                {"role": "user", "content": user_input}
            ]
        )
        
        validation_result = validation_response.choices[0].message.content.strip()
        
        if "ask again" not in validation_result.lower():
            # Store the validated input
            setattr(user, current_step.field, user_input)
            user.onboarding_step += 1
            db.session.commit()
            
            # Get next step
            next_step = ONBOARDING_STEPS.get(user.onboarding_step)
            if next_step:
                current_step = next_step
            else:
                return success_response({
                    "response": "Thank you for completing the onboarding! We're excited to have you on board.",
                    "user_id": user.uid
                })
        else:
            # Use the validation message as the response
            return success_response({
                "response": validation_result,
                "user_id": user.uid
            })

    # Generate contextual response
    response = client.chat.completions.create(
        model=OPENAI_MODEL_NAME,
        messages=[
            {"role": "system", "content": current_step.system_context},
            {"role": "user", "content": user_input or ""},
            {"role": "assistant", "content": current_step.prompt}
        ]
    )

    assistant_reply = response.choices[0].message.content.strip()
    return success_response({"response": assistant_reply, "user_id": user.uid})
    


# UTILS
def success_response(data: dict = {}, status_code: int = 200):
    return jsonify({"success": True, "data": data, "status_code":status_code})

def error_response(message: str = "", data: dict = {}, status_code: int = 400):
    return jsonify({"success": False, "message": message, "status_code":status_code, "data": data})


@dataclass
class OnboardingStep:
    prompt: str
    field: str
    system_context: str
    validation_prompt: str

# Define onboarding steps with context-aware prompts
ONBOARDING_STEPS = {
    0: OnboardingStep(
        prompt="Hi there! I'd love to get to know you better. What's your first name?",
        field="firstname",
        system_context="You are a friendly onboarding assistant. You need to collect the user's first name.",
        validation_prompt="Validate if this is a proper first name. If not, ask again politely."
    ),
    1: OnboardingStep(
        prompt="Thanks! And what's your last name?",
        field="lastname",
        system_context="You are a friendly onboarding assistant. You are collecting the user's last name. Be friendly but professional.",
        validation_prompt="Validate if this is a proper last name. If not, ask again politely."
    ),
    2: OnboardingStep(
        prompt="Which company do you work for?",
        field="company",
        system_context="You are a friendly onboarding assistant. You are collecting the user's company name. If they don't provide one, ask if they're self-employed or a freelancer.",
        validation_prompt="Validate if this looks like a company name. If not, ask for clarification."
    ),
    3: OnboardingStep(
        prompt="What's your primary job function? (e.g., Engineering, Marketing, Sales, Product)",
        field="job_function",
        system_context="You are a friendly onboarding assistant. You are collecting the user's job function. Help categorize their role into a standard department.",
        validation_prompt="Check if this is a standard job function. If unclear, ask for clarification."
    ),
    4: OnboardingStep(
        prompt="What's your specific job title?",
        field="job_title",
        system_context="You are a friendly onboarding assistant. You are collecting the user's specific job title. This should align with their previously mentioned job function.",
        validation_prompt="Validate if this job title aligns with their job function. If not, ask for clarification."
    ),
    5: OnboardingStep(
        prompt="Last question - how did you hear about us?",
        field="heard_about_us",
        system_context="You are a friendly onboarding assistant. You are collecting information about how the user discovered the product. Be casual and friendly.",
        validation_prompt="Accept any reasonable response about how they heard about the product."
    )
}