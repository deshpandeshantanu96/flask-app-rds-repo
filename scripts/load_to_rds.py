import pandas as pd
from sqlalchemy import create_engine, exc
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_rds_config():
    """Get RDS configuration with robust port handling"""
    try:
        # Get port with fallbacks
        port_str = os.getenv("DB_PORT")
        if not port_str or not port_str.isdigit():
            logger.warning("DB_PORT not set or invalid, using default 3306")
            port = 3306
        else:
            port = int(port_str)

        config = {
            "host": os.getenv("DB_HOST"),
            "db_name": os.getenv("DB_NAME"),
            "username": os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
            "port": port
        }

        # Validate required fields
        required = ["host", "db_name", "username", "password"]
        missing = [field for field in required if not config[field]]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")

        return config

    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        raise

def create_db_engine(config):
    """Create engine with enhanced error handling"""
    try:
        conn_str = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['db_name']}"
        )
        
        return create_engine(
            conn_str,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
    except Exception as e:
        logger.error(f"Engine creation failed: {str(e)}")
        raise

def load_data_to_rds():
    try:
        config = get_rds_config()
        engine = create_db_engine(config)
        
        # Verify connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        # Load data - using fixed table name 'customers'
        df = pd.read_csv('customers-10000.csv')
        df.to_sql(
            name='customers',  # Hardcoded table name
            con=engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        
        logger.info(f"Successfully loaded {len(df)} rows to 'customers' table")
        return True
        
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    return False

if __name__ == "__main__":
    if load_data_to_rds():
        exit(0)
    exit(1)