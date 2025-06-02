from flask import Blueprint, request, jsonify
from flask_login import current_user
from .models import PhoneNumber
from ..extensions import db
from . import phone_numbers
from ..security.routes import auth
import logging


@phone_numbers.route('/', methods=['POST'])
@auth.login_required
def add_phone_number():
    data = request.get_json()

    current_user = auth.current_user()
    current_profile = current_user.profile
    
 
    phone_number_value = data.get('phone_number') 
    account_sid_value = data.get('account_sid') 
    auth_token_value = data.get('auth_token') 
    
    if not phone_number_value or not account_sid_value or not auth_token_value:
        return jsonify({'error': 'Missing required fields'}), 400
        
    phone_number = PhoneNumber(
        phone_number=phone_number_value,
        account_sid=account_sid_value,
        auth_token=auth_token_value,
        profile_id=current_profile.id
    )
    
    try:
        db.session.add(phone_number)
        db.session.commit()
        return jsonify({
            'message': 'Phone number added successfully',
            'phone_number': phone_number.phone_number
        }), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding phone number: {str(e)}")
        return jsonify({'error': str(e)}), 400


@phone_numbers.route('/<int:phone_number_id>', methods=['DELETE'])
@auth.login_required
def remove_phone_number(phone_number_id):
    phone_number = PhoneNumber.query.get_or_404(phone_number_id)

    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if phone_number.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        db.session.delete(phone_number)
        db.session.commit()
        return jsonify({'message': 'Phone number removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@phone_numbers.route('/', methods=['GET'])
@auth.login_required
def get_phone_numbers():
    current_user = auth.current_user()
    current_profile = current_user.profile

    try:
        phone_numbers = PhoneNumber.query.filter_by(profile_id=current_profile.id).all()
        
        return jsonify([{
            'id': phone.id,
            'phone_number': phone.phone_number,
            'account_sid': phone.account_sid,
            'is_verified': phone.is_verified,
            'created_at': phone.created_at,
            'updated_at': phone.updated_at
        } for phone in phone_numbers]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@phone_numbers.route('/<int:phone_number_id>', methods=['PUT'])
@auth.login_required
def update_phone_number(phone_number_id):
    try:
        # Get the phone number
        phone_number = PhoneNumber.query.get_or_404(phone_number_id)
        
        # Verify ownership
        current_user = auth.current_user()
        current_profile = current_user.profile
        
        if phone_number.profile_id != current_profile.id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get update data
        data = request.get_json()
        
        # Update fields if provided
        if 'phone_number' in data:
            phone_number.phone_number = data['phone_number']
        if 'account_sid' in data:
            phone_number.account_sid = data['account_sid']
        if 'auth_token' in data:
            phone_number.auth_token = data['auth_token']
        if 'is_verified' in data:
            phone_number.is_verified = data['is_verified']
            
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Phone number updated successfully',
            'phone_number': {
                'id': phone_number.id,
                'phone_number': phone_number.phone_number,
                'account_sid': phone_number.account_sid,
                'is_verified': phone_number.is_verified,
                'created_at': phone_number.created_at,
                'updated_at': phone_number.updated_at
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating phone number: {str(e)}")
        return jsonify({'error': str(e)}), 400
