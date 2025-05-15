from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import mysql.connector
import os
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()  

# RDS MySQL Configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", "3306")),
    # "ssl": {
    #     "ca": "/path/to/aws-rds-ca-cert.pem"  # For AWS RDS SSL
    # }
}

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def read_users(request: Request):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return templates.TemplateResponse("index.html", {"request": request, "users": users})


@app.get("/user/{customer_id}", response_class=HTMLResponse)
async def read_user(request: Request, customer_id: str):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE `customer_id` = %s", (customer_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return templates.TemplateResponse("user.html", {"request": request, "user": user})

    except Exception as e:
        print("❌ ERROR in /user/{customer_id} route:", str(e))
        return HTMLResponse(f"<h2>Internal Server Error</h2><pre>{str(e)}</pre>", status_code=500)


@app.post("/user/{customer_id}/update")
async def update_user(customer_id: str, first_name: str = Form(...), last_name: str = Form(...)):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE customers 
        SET `first_name` = %s, `last_name` = %s 
        WHERE `customer_id` = %s
    """, (first_name, last_name, customer_id))
    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse(url=f"/user/{customer_id}", status_code=303)


@app.post("/user/{customer_id}/delete")
async def delete_user(customer_id: str):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE `Customer Id` = %s", (customer_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="127.0.0.1", port=8000, reload=True)
