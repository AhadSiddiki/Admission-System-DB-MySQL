from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import date, datetime, timedelta
import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
import base64
import hashlib
from enum import Enum

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="University Admission API",
    description="API for managing university admission system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Security setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database connection pool
connection_pool = pooling.MySQLConnectionPool(
    pool_name="uni_admission_pool",
    pool_size=5,
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "uni_admission_371")
)


# Pydantic models for request/response handling
class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class PaymentStatus(str, Enum):
    PAID = "Paid"
    PENDING = "Pending"
    FAILED = "Failed"


class ResultStatus(str, Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    PENDING = "Pending"


class ApplicantBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Gender
    phone_number: Optional[str] = None
    email: EmailStr
    address: Optional[str] = None
    ssc_gpa: float = Field(..., ge=0.0, le=5.0)
    hsc_gpa: float = Field(..., ge=0.0, le=5.0)


class ApplicantCreate(ApplicantBase):
    password: str


class ApplicantLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class Applicant(ApplicantBase):
    applicant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ExamCenter(BaseModel):
    center_id: Optional[int] = None
    center_name: str
    center_address: str


class ExamUnit(BaseModel):
    unit_id: Optional[int] = None
    unit_code: str
    center_id: int
    exam_date: date
    exam_time: str
    exam_duration: Optional[int] = 60


class AdmitCardBase(BaseModel):
    applicant_id: int
    unit_id: int
    room_no: Optional[int] = None


class AdmitCardCreate(AdmitCardBase):
    pass


class AdmitCard(AdmitCardBase):
    exam_roll: int
    issued_at: datetime
    applicant_photo: Optional[str] = None  # Base64 encoded photo

    class Config:
        orm_mode = True


class PaymentBase(BaseModel):
    applicant_id: int
    fee_amount: float
    payment_status: PaymentStatus = PaymentStatus.PENDING


class PaymentCreate(PaymentBase):
    payment_datetime: Optional[datetime] = None


class Payment(PaymentBase):
    payment_id: int
    created_at: datetime
    payment_datetime: Optional[datetime] = None

    class Config:
        orm_mode = True


class ResultBase(BaseModel):
    applicant_id: int
    unit_id: int
    marks_obtained: Optional[float] = None
    status: ResultStatus = ResultStatus.PENDING


class ResultCreate(ResultBase):
    pass


class Result(ResultBase):
    result_id: int
    total_marks: int
    result_published: Optional[datetime] = None

    class Config:
        orm_mode = True


class ApplicantDashboard(BaseModel):
    applicant_id: int
    first_name: str
    last_name: str
    ssc_gpa: float
    hsc_gpa: float
    unit_code: str
    marks_obtained: float
    result_status: str
    merit_position: str


# Helper functions
def get_db_connection():
    return connection_pool.get_connection()


# SHA-256 Hashing Functions
def get_password_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password


def authenticate_user(email: str, password: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM applicant_login WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user or not verify_password(password, user["password_hash"]):
            return False

        # Update last login
        cursor.execute("UPDATE applicant_login SET last_login = NOW() WHERE email = %s", (email,))
        conn.commit()

        # Get applicant info
        cursor.execute("SELECT * FROM applicant_info WHERE email = %s", (email,))
        applicant_info = cursor.fetchone()

        return applicant_info
    finally:
        cursor.close()
        conn.close()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except jwt.PyJWTError:
        raise credentials_exception

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM applicant_info WHERE email = %s", (token_data.email,))
        user = cursor.fetchone()
        if user is None:
            raise credentials_exception
        return user
    finally:
        cursor.close()
        conn.close()


# API Endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        # Log the detailed error
        print(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during authentication: {str(e)}"
        )


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_applicant(applicant: ApplicantCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # First, insert into applicant_info
        applicant_data = applicant.dict(exclude={"password"})

        placeholders = ", ".join(["%s"] * len(applicant_data))
        columns = ", ".join(applicant_data.keys())
        values = list(applicant_data.values())

        query = f"INSERT INTO applicant_info ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        # Then, insert into applicant_login
        password_hash = get_password_hash(applicant.password)
        cursor.execute(
            "INSERT INTO applicant_login (email, password_hash) VALUES (%s, %s)",
            (applicant.email, password_hash)
        )

        conn.commit()

        return {"message": "Applicant registered successfully"}
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno == 1062:  # Duplicate key error
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/applicants/me", response_model=Applicant)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.get("/dashboard", response_model=ApplicantDashboard)
async def get_applicant_dashboard(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM applicant_dashboard WHERE applicant_id = %s",
            (current_user["applicant_id"],)
        )
        dashboard = cursor.fetchone()

        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard information not found")

        return dashboard
    finally:
        cursor.close()
        conn.close()


@app.post("/upload-photo")
async def upload_applicant_photo(
        photo: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Read the file content
        photo_data = await photo.read()

        # Update the applicant_photo in admit_card
        cursor.execute(
            "UPDATE admit_card SET applicant_photo = %s WHERE applicant_id = %s",
            (photo_data, current_user["applicant_id"])
        )

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Admit card not found")

        return {"message": "Photo uploaded successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading photo: {str(e)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/admit-card", response_model=AdmitCard)
async def get_admit_card(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM admit_card WHERE applicant_id = %s",
            (current_user["applicant_id"],)
        )
        admit_card = cursor.fetchone()

        if not admit_card:
            raise HTTPException(status_code=404, detail="Admit card not found")

        # Convert the BLOB to base64 if exists
        if admit_card["applicant_photo"]:
            admit_card["applicant_photo"] = base64.b64encode(admit_card["applicant_photo"]).decode("utf-8")

        return admit_card
    finally:
        cursor.close()
        conn.close()


@app.get("/exam-centers", response_model=List[ExamCenter])
async def get_exam_centers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM exam_center")
        centers = cursor.fetchall()

        return centers
    finally:
        cursor.close()
        conn.close()


@app.get("/exam-units", response_model=List[ExamUnit])
async def get_exam_units():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM exam_units")
        units = cursor.fetchall()

        return units
    finally:
        cursor.close()
        conn.close()


@app.post("/make-payment", response_model=Payment)
async def make_payment(payment: PaymentCreate, current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Override applicant_id with current user
        payment_data = payment.dict()
        payment_data["applicant_id"] = current_user["applicant_id"]

        # Set payment datetime to now if not provided
        if payment_data.get("payment_datetime") is None:
            payment_data["payment_datetime"] = datetime.now()

        placeholders = ", ".join(["%s"] * len(payment_data))
        columns = ", ".join(payment_data.keys())
        values = list(payment_data.values())

        query = f"INSERT INTO payment ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        payment_id = cursor.lastrowid
        conn.commit()

        # Get the newly created payment
        cursor.execute("SELECT * FROM payment WHERE payment_id = %s", (payment_id,))
        new_payment = cursor.fetchone()

        return new_payment
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


@app.get("/results", response_model=List[Result])
async def get_results(current_user: dict = Depends(get_current_user)):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM result WHERE applicant_id = %s",
            (current_user["applicant_id"],)
        )
        results = cursor.fetchall()

        return results
    finally:
        cursor.close()
        conn.close()


# Admin endpoints (would need additional authorization)
@app.post("/admin/exam-centers", response_model=ExamCenter, status_code=status.HTTP_201_CREATED)
async def create_exam_center(center: ExamCenter):
    # In a real system, this would have admin authorization
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        center_data = center.dict(exclude={"center_id"})

        placeholders = ", ".join(["%s"] * len(center_data))
        columns = ", ".join(center_data.keys())
        values = list(center_data.values())

        query = f"INSERT INTO exam_center ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        center_id = cursor.lastrowid
        conn.commit()

        return {**center.dict(), "center_id": center_id}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/admin/exam-units", response_model=ExamUnit, status_code=status.HTTP_201_CREATED)
async def create_exam_unit(unit: ExamUnit):
    # In a real system, this would have admin authorization
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        unit_data = unit.dict(exclude={"unit_id"})

        placeholders = ", ".join(["%s"] * len(unit_data))
        columns = ", ".join(unit_data.keys())
        values = list(unit_data.values())

        query = f"INSERT INTO exam_units ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        unit_id = cursor.lastrowid
        conn.commit()

        return {**unit.dict(), "unit_id": unit_id}
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/admin/admit-cards", response_model=AdmitCard, status_code=status.HTTP_201_CREATED)
async def create_admit_card(admit_card: AdmitCardCreate):
    # In a real system, this would have admin authorization
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Generate exam roll
        cursor.execute("SELECT MAX(exam_roll) AS max_roll FROM admit_card")
        max_roll = cursor.fetchone()["max_roll"] or 220430  # Default to 220430 if no previous roll
        new_roll = max_roll + 1

        # Insert admit card
        admit_card_data = admit_card.dict()
        admit_card_data["exam_roll"] = new_roll

        placeholders = ", ".join(["%s"] * len(admit_card_data))
        columns = ", ".join(admit_card_data.keys())
        values = list(admit_card_data.values())

        query = f"INSERT INTO admit_card ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        conn.commit()

        # Get the newly created admit card
        cursor.execute("SELECT * FROM admit_card WHERE exam_roll = %s", (new_roll,))
        new_admit_card = cursor.fetchone()

        # Convert BLOB to base64 if exists
        if new_admit_card["applicant_photo"]:
            new_admit_card["applicant_photo"] = base64.b64encode(new_admit_card["applicant_photo"]).decode("utf-8")

        return new_admit_card
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


@app.post("/admin/results", response_model=Result, status_code=status.HTTP_201_CREATED)
async def create_result(result: ResultCreate):
    # In a real system, this would have admin authorization
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        result_data = result.dict()

        # If marks are present and status is not set, determine status
        if result_data.get("marks_obtained") is not None and result_data.get("status") == ResultStatus.PENDING:
            # Assuming passing mark is 40% of 80
            result_data["status"] = ResultStatus.PASSED if result_data["marks_obtained"] >= 32 else ResultStatus.FAILED

        # Set result_published timestamp if status is Passed or Failed
        if result_data.get("status") in [ResultStatus.PASSED, ResultStatus.FAILED]:
            result_data["result_published"] = datetime.now()

        placeholders = ", ".join(["%s"] * len(result_data))
        columns = ", ".join(result_data.keys())
        values = list(result_data.values())

        query = f"INSERT INTO result ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        result_id = cursor.lastrowid
        conn.commit()

        # Get the newly created result
        cursor.execute("SELECT * FROM result WHERE result_id = %s", (result_id,))
        new_result = cursor.fetchone()

        return new_result
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(err)}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)