"""
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
"""

import pandas as pd
from sqlalchemy import create_engine, exc, text
import os
import logging
import sys
import boto3
import json
import time
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RDSConnectionManager:
    """Handles secure RDS connections with Secrets Manager integration"""
    
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 5
        
    def get_secret(self, secret_name, region_name="us-east-1"):
        """Fetch secret from AWS Secrets Manager with retry logic"""
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        for attempt in range(self.max_retries):
            try:
                response = client.get_secret_value(SecretId=secret_name)
                if 'SecretString' in response:
                    try:
                        return json.loads(response['SecretString'])
                    except json.JSONDecodeError:
                        return response['SecretString']
                return response.get('SecretBinary')
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to retrieve secret after {self.max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Secret retrieval attempt {attempt + 1} failed, retrying...")
                time.sleep(self.retry_delay)
    
    def get_rds_config(self):
        """Get validated RDS configuration with fallbacks"""
        try:
            config = {
                "host": os.getenv("DB_HOST"),
                "port": int(os.getenv("DB_PORT", "3306")),
                "db_name": os.getenv("DB_NAME"),
                "username": os.getenv("DB_USERNAME"),
                "secret_name": os.getenv("RDS_PASSWORD_SECRET_NAME"),
                "ssl_ca": os.getenv("RDS_SSL_CA_PATH", "/etc/ssl/certs/ca-certificates.crt")
            }
            
            # Validate required fields
            missing = [k for k, v in config.items() if not v and k != "port"]
            if missing:
                raise ValueError(f"Missing required config: {missing}")
            
            # Get password from Secrets Manager
            secret = self.get_secret(config["secret_name"])
            config["password"] = secret.get("password") if isinstance(secret, dict) else secret
            
            if not config["password"]:
                raise ValueError("No password found in secret")
                
            return config
            
        except ValueError as ve:
            logger.error(f"Configuration validation error: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Configuration error: {str(e)}")
            raise
    
    def create_engine(self, config):
        """Create SQLAlchemy engine with robust error handling"""
        connection_string = (
            f"mysql+pymysql://{quote_plus(config['username'])}:{quote_plus(config['password'])}"
            f"@{config['host']}:{config['port']}/{config['db_name']}"
            "?charset=utf8mb4"
            "&connect_timeout=10"
            "&ssl_ca={config['ssl_ca']}"
        )
        
        for attempt in range(self.max_retries):
            try:
                engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_size=5,
                    max_overflow=10,
                    echo=False
                )
                
                # Test connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                logger.info("Database connection established")
                return engine
                
            except exc.SQLAlchemyError as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(self.retry_delay * (attempt + 1))

def load_data_to_rds():
    """Main data loading function with comprehensive error handling"""
    try:
        manager = RDSConnectionManager()
        
        # 1. Get configuration
        config = manager.get_rds_config()
        logger.info("RDS configuration validated")
        
        # 2. Establish connection
        engine = manager.create_engine(config)
        
        # 3. Load and transform data
        df = pd.read_csv('customers-10000.csv')
        logger.info(f"Loaded {len(df)} records from CSV")
        
        # 4. Write to database
        df.to_sql(
            name='customers',
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000,
            method='multi'
        )
        
        logger.info("Data successfully loaded to RDS")
        return True
        
    except pd.errors.EmptyDataError:
        logger.error("Input CSV file is empty or invalid")
    except exc.SQLAlchemyError as e:
        logger.error(f"Database operation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.exception(e)  # Log full stack trace
        
    return False

if __name__ == "__main__":
    try:
        success = load_data_to_rds()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)