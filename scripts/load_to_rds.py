import pandas as pd
from sqlalchemy import create_engine
import boto3
from python_terraform import Terraform
import json

def get_rds_config_from_tf_state():
    tf = Terraform(working_dir="../terraform")  # adjust if needed
    return_code, stdout, stderr = tf.output()
    
    if return_code != 0:
        raise Exception(f"Terraform output failed: {stderr}")
    
    outputs = json.loads(stdout)
    return outputs

def get_secret():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='your_secret_name')
    return response['SecretString']

# RDS connection details
db_config = get_rds_config_from_tf_state()
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