import pandas as pd
from sqlalchemy import create_engine
import boto3
from python_terraform import Terraform
import json
import os

def get_rds_config():
    """Parse Terraform outputs from JSON"""
    tf_outputs = json.loads(os.getenv("TF_OUTPUTS"))
    return {
        "host": tf_outputs["rds_endpoint"]["value"],
        "secret_arn": tf_outputs["rds_secret_arn"]["value"],
        "db_name": tf_outputs["rds_db_name"]["value"],
        "username": tf_outputs["rds_username"]["value"]
        }

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='your_secret_name')
    return response['SecretString']

# RDS connection details
db_config = get_rds_config()
# Create SQLAlchemy engine
engine = create_engine(f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}")

# Read CSV
df = pd.read_csv('customers-10000.csv')

# Write to RDS
df.to_sql(
    name='your_table_name',
    con=engine,
    if_exists='append',  # or 'replace' to drop and recreate
    index=False,
    chunksize=1000  # For large files
)

print("Data loaded successfully!")