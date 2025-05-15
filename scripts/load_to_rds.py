import pandas as pd
from sqlalchemy import create_engine, exc
import os
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_rds_config():
    """Get RDS configuration from environment variables"""
    config = {
        "host": os.getenv("DB_HOST"),
        "db_name": os.getenv("DB_NAME"),
        "username": os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
        "port": os.getenv("DB_PORT", "3306"),  # Default to MySQL port
        "table_name": os.getenv("DB_TABLE_NAME", "customers")  # Default table name
    }
    
    # Validate required configuration
    missing = [k for k, v in config.items() if v is None and k != "table_name"]
    if missing:
        raise ValueError(f"Missing required database configuration: {', '.join(missing)}")
    
    return config

def create_db_engine(config):
    """Create SQLAlchemy engine with connection pooling"""
    try:
        connection_string = (
            f"mysql+pymysql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['db_name']}"
        )
        
        engine = create_engine(
            connection_string,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "connect_timeout": 5
            }
        )
        return engine
    except Exception as e:
        logger.error(f"Error creating database engine: {str(e)}")
        raise

def load_data_to_rds():
    try:
        # Get configuration
        db_config = get_rds_config()
        
        # Create database engine
        engine = create_db_engine(db_config)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            logger.info("Database connection test successful")
        
        # Read CSV
        df = pd.read_csv('customers-10000.csv')
        logger.info(f"Loaded CSV with {len(df)} rows")
        
        # Write to RDS
        df.to_sql(
            name=db_config['table_name'],
            con=engine,
            if_exists='append',  # or 'replace' to drop and recreate
            index=False,
            chunksize=1000,
            method='multi'  # Faster inserts for MySQL
        )
        
        logger.info(f"Data loaded successfully to table {db_config['table_name']}")
        return True
        
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    if load_data_to_rds():
        print("Data loading completed successfully!")
    else:
        print("Data loading failed. Check logs for details.")
        exit(1)