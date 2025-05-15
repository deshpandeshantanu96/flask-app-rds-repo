import pandas as pd
from sqlalchemy import create_engine, exc, text
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        config = {
            "host": os.getenv("DB_HOST"),
            "db_name": os.getenv("DB_NAME"),
            "username": os.getenv("DB_USERNAME"),
            "password": os.getenv("DB_PASSWORD"),
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