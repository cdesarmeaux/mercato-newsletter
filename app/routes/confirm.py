from flask import Blueprint, request, jsonify
from app.utils.email import is_valid_email
import boto3

confirm_bp = Blueprint('confirm', __name__)

s3 = boto3.client('s3', region_name='eu-west-1')
bucket_name = 'your_bucket_name'

@confirm_bp.route('/confirm', methods=['GET'])
def confirm_email():
    email = request.args.get('email')
    
    if not email or not is_valid_email(email):
        return jsonify({'message': 'Invalid email'}), 400
    
    # Move the file in S3 from unverified to verified
    copy_source = {'Bucket': bucket_name, 'Key': f'subscribers/unverified/{email}'}
    s3.copy_object(CopySource=copy_source, Bucket=bucket_name, Key=f'subscribers/verified/{email}')
    s3.delete_object(Bucket=bucket_name, Key=f'subscribers/unverified/{email}')
    
    return jsonify({'message': 'Email verified successfully'}), 200
