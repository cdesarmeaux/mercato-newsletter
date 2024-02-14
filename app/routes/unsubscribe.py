from flask import Blueprint, request, jsonify, render_template
import boto3

unsubscribe_bp = Blueprint("unsubscribe", __name__)

s3 = boto3.client("s3")
bucket_name = "thetransferledger-subscribers"


@unsubscribe_bp.route("/unsubscribe", methods=["POST"])
def unsubscribe_email():
    email = request.json.get("email")

    # Check if the email is in the S3 bucket
    try:
        s3.head_object(Bucket=bucket_name, Key=f"subscribers/verified/{email}")
    except Exception as e:
        # If the email does not exist in the S3 bucket, return an error
        return jsonify({"message": f"Email {email} is not subscribed."}), 400

    # If the email exists, delete it from the S3 bucket
    s3.delete_object(Bucket=bucket_name, Key=f"subscribers/verified/{email}")

    # Return the confirmation HTML file
    return render_template("unsubscribe_confirmation.html")
