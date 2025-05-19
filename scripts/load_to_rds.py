import pandas as pd
from sqlalchemy import create_engine, exc, text
import os
import logging
import sys
import boto3
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name="us-east-1"):
    """
    Fetch secret value from AWS Secrets Manager.
    Returns the secret string or dict.
    """
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
        raise

    secret = get_secret_value_response.get('SecretString')
    if secret:
        try:
            return json.loads(secret)  # try to parse JSON
        except json.JSONDecodeError:
            return secret  # return as string if not JSON
    else:
        # Secret binary case (rare)
        return get_secret_value_response.get('SecretBinary')

def get_rds_config():
    """Get RDS configuration with robust error handling"""
    try:
        # Get port with proper conversion
        port_str = os.getenv("DB_PORT", "3306")
        try:
            port = int(port_str)
        except ValueError:
            logger.warning(f"Invalid port '{port_str}', using default 3306")
            port = 3306

        # Fetch password secret name from env or hardcode
        secret_name = os.getenv("RDS_PASSWORD_SECRET_NAME")
        if not secret_name:
            raise ValueError("RDS_PASSWORD_SECRET_NAME env var is not set")

        secret_value = get_secret(secret_name)
        # If secret is JSON, expect {"password": "actual_password"}
        if isinstance(secret_value, dict):
            password = secret_value.get("password")
            if not password:
                raise ValueError(f"No 'password' field found in secret {secret_name}")
        else:
            password = secret_value

        config = {
            "host": os.getenv("DB_HOST"),
            "db_name": os.getenv("DB_NAME"),
            "username": os.getenv("DB_USERNAME"),
            "password": password,
            "port": port
        }

        # Validate required configuration
        missing = [k for k, v in config.items() if not v and k != "port"]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        return config

    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        raise

def create_db_engine(config):
    """Create SQLAlchemy engine with proper connection testing"""
    try:
        connection_string = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['db_name']}"
        )
        
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        # Test connection properly using text()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            
        return engine
        
    except exc.SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Engine creation failed: {str(e)}")
        raise

def load_data_to_rds():
    try:
        # Get configuration
        db_config = get_rds_config()
        
        # Create and test connection
        engine = create_db_engine(db_config)
        logger.info("Database connection established successfully")
        
        # Read CSV
        df = pd.read_csv('customers-10000.csv')
        logger.info(f"Loaded CSV with {len(df)} rows")
        
        # Write to RDS
        df.to_sql(
            name='customers',
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        
        logger.info("Data loaded successfully!")
        return True
        
    except pd.errors.EmptyDataError:
        logger.error("CSV file is empty or invalid")
    except exc.SQLAlchemyError as e:
        logger.error(f"Database operation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    
    return False

if __name__ == "__main__":
    if load_data_to_rds():
        sys.exit(0)
    sys.exit(1)