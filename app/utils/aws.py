import boto3

def get_ssm_parameter(boto3_client: boto3.client, name: str) -> str:
    response = boto3_client.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']