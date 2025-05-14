import pandas as pd
from sqlalchemy import create_engine
import boto3
from python_terraform import Terraform

def get_rds_config_from_tf_state():
    tf = Terraform(working_dir='.')
    outputs = tf.output()
    
    return {
        'host': outputs['rds_instance_endpoint']['value'],
        'secret_arn': outputs['rds_secret_arn']['value'],
        'database': outputs['rds_db_name']['value'],
        'username': outputs['rds_username']['value']
    }

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