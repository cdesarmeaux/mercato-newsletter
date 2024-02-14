import boto3

from flask import Blueprint, request, jsonify, render_template
from itsdangerous import URLSafeTimedSerializer

from app.utils.email import is_valid_email
from app.utils.aws import get_ssm_parameter

register_bp = Blueprint('register', __name__)

# Initialize AWS clients and variables
s3 = boto3.client('s3',region_name='eu-west-1')
ses = boto3.client('ses', region_name='eu-west-1')
ssm = boto3.client('ssm', region_name='eu-west-1')
bucket_name = 'thetransferledger-subscribers'
from_email = 'daily@thetransferledger.com'


def get_serializer():
    secret_key = get_ssm_parameter(ssm, '/newsletter/email_confirm_link_secret_key')
    return URLSafeTimedSerializer(secret_key)

@register_bp.route('/register', methods=['POST'])
def register_email():
    email = request.json.get('email')
    
    if not email or not is_valid_email(email):
        return jsonify({'message': 'Invalid email'}), 400
    
    # Upload to S3
    s3.put_object(Bucket=bucket_name, Key=f'subscribers/unverified/{email}', Body='')
    
    # Generate confirmation token
    serializer = get_serializer()
    token = serializer.dumps(email, salt='email-confirmation')
    confirmation_link = f"http://your_api_url/confirm?token={token}"
    
    # Render the email content using the template
    email_content = render_template('email_confirmation.html', confirmation_link=confirmation_link)
    
    # Send email using Amazon SES
    ses.send_email(
        Source=from_email,
        Destination={
            'ToAddresses': [email]
        },
        Message={
            'Subject': {'Data': 'Confirm Your Email'},
            'Body': {'Html': {'Data': email_content}}
        }
    )
    
    return jsonify({'message': 'Email sent for confirmation'}), 200

