from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from typing import Dict, ClassVar
from pydantic import BaseModel, field_validator, ValidationError
import secrets
from contextlib import contextmanager
from passlib.context import CryptContext
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Generate secret key if not in environment (for development only)
if not os.getenv("SESSION_SECRET"):
    generated_key = secrets.token_urlsafe(32)
    logger.warning(f"Using generated session key for development: {generated_key}")
    os.environ["SESSION_SECRET"] = generated_key

# Add SessionMiddleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET"),
    session_cookie="secure_session",
    https_only=os.getenv("ENVIRONMENT") == "production",  # True in production
    max_age=3600,  # 1 hour session duration
    same_site="lax"
)

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# Admin credentials (in production, use database authentication)
ADMIN_CREDENTIALS = {
    "admin": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123"))
}

templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

# --- Models ---
class UserUpdateForm(BaseModel):
    first_name: str
    last_name: str
    re_module: ClassVar = re  # Properly declare the re module as ClassVar

    @field_validator('first_name')
    def validate_first_name(cls, v):
        v = v.strip()  # Trim any leading/trailing spaces
        if len(v) < 2 or len(v) > 50:
            raise ValueError('First name must be between 2 and 50 characters')
        if not cls.re_module.match(r"^[A-Za-z\s'-]+$", v):  # Use cls.re_module
            raise ValueError('First name must contain only alphabets, spaces, apostrophes, or hyphens')
        return v

    @field_validator('last_name')
    def validate_last_name(cls, v):
        v = v.strip()  # Trim any leading/trailing spaces
        if len(v) < 2 or len(v) > 50:
            raise ValueError('Last name must be between 2 and 50 characters')
        if not cls.re_module.match(r"^[A-Za-z\s'-]+$", v):  # Use cls.re_module
            raise ValueError('Last name must contain only alphabets, spaces, apostrophes, or hyphens')
        return v

# --- Database Utilities ---
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = mysql.connector.connect(**db_config)
        yield conn
    except Error as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    finally:
        if conn and conn.is_connected():
            conn.close()

@contextmanager
def get_db_cursor(conn):
    """Context manager for database cursors"""
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True, buffered=True)
        yield cursor
    finally:
        if cursor:
            cursor.close()

# --- Authentication ---
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

async def authenticate_admin(
    credentials: HTTPBasicCredentials = Depends(security)
) -> bool:
    """Authenticate admin user"""
    username = credentials.username
    password = credentials.password
    
    if username in ADMIN_CREDENTIALS and verify_password(
        password, ADMIN_CREDENTIALS[username]
    ):
        return True
    
    logger.warning(f"Failed login attempt for user: {username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def read_users(request: Request):
    """Home page showing all users"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute("SELECT * FROM customers")
                users = cursor.fetchall()
        
        is_admin = request.session.get("is_admin", False)
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "users": users, "is_admin": is_admin}
        )
    except Exception as e:
        logger.error(f"Error in read_users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/user/{user_id}", response_class=HTMLResponse)
async def read_user(request: Request, user_id: str):
    """View single user details"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(
                    "SELECT * FROM customers WHERE `Customer Id` = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if not user:
                    logger.info(f"Looking up user with Customer Id: {user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="User not found"
                    )
                
                is_admin = request.session.get("is_admin", False)
                return templates.TemplateResponse(
                    "user.html",
                    {"request": request, "user": user, "is_admin": is_admin}
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in read_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/user/{user_id}/update")
async def update_user(
    request: Request,
    user_id: str,
    first_name: str = Form(...),
    last_name: str = Form(...)
):
    """Update user information"""
    try:
        form_data = UserUpdateForm(first_name=first_name, last_name=last_name)
        # If validation passes, proceed with DB update
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(
                    """UPDATE customers 
                    SET `First Name` = %s, `Last Name` = %s 
                    WHERE `Customer Id` = %s""",
                    (form_data.first_name, form_data.last_name, user_id)
                )
                conn.commit()
        
        return RedirectResponse(
            url=f"/user/{user_id}",
            status_code=status.HTTP_303_SEE_OTHER
        )

    except ValidationError as e:
        # Extract all error messages from the ValidationError
        errors = e.errors()
        error_msgs = [err['msg'] for err in errors]
        combined_error_msg = "; ".join(error_msgs)
        
        # Reload user data from DB (optional)
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute("SELECT * FROM customers WHERE `Customer Id` = %s", (user_id,))
                user = cursor.fetchone()

        # Return error messages to the template
        return templates.TemplateResponse(
            "user.html",
            {
                "request": request,
                "user": user,
                "errors": {"form": combined_error_msg},
                "is_admin": request.session.get("is_admin", False)
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in update_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    
@app.get("/user/{user_id}/confirm-delete", response_class=HTMLResponse)
async def confirm_delete_user(request: Request, user_id: str):
    """Render confirmation page for deleting a user"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(
                    "SELECT * FROM customers WHERE `Customer Id` = %s",
                    (user_id,)
                )
                user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return templates.TemplateResponse(
            "confirm_delete.html",
            {"request": request, "user": user}
        )
    except Exception as e:
        logger.error(f"Error in confirm_delete_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/user/{user_id}/delete")
async def delete_user(request: Request, user_id: str):
    """Delete a user by Customer Id"""
    try:
        logger.info(f"Attempting to delete user with Customer Id: {user_id}")

        with get_db_connection() as conn:
            with get_db_cursor(conn) as cursor:
                cursor.execute(
                    "DELETE FROM customers WHERE `Customer Id` = %s",
                    (user_id,)
                )
                conn.commit()

        logger.info(f"Successfully deleted user with Customer Id: {user_id}")

        return RedirectResponse(
            url="/",
            status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"Error in delete_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# --- Admin Routes ---
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def perform_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Process admin login"""
    try:
        if (username in ADMIN_CREDENTIALS and 
            verify_password(password, ADMIN_CREDENTIALS[username])):
            
            request.session["is_admin"] = True
            return RedirectResponse(
                url="/",
                status_code=status.HTTP_303_SEE_OTHER
            )
        
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid credentials"
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        logger.error(f"Error in perform_login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/logout")
async def logout(request: Request):
    """Admin logout"""
    request.session.clear()
    return RedirectResponse(
        url="/",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- Main ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development"
    )