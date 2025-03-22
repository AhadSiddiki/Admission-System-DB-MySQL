# A University Admission Test Data Management System using MySQL.
# University Admission Database System Documentation
## Database: uni_admission_371

## Overview
This database system manages the university admission process, handling applicant information, exam scheduling, payments, and results.

## Database Schema

### 1. Core Tables

#### applicant_info
- Primary table storing applicant details
- Fields:
  ```sql
  applicant_id (Primary Key, Auto Increment)
  first_name, last_name
  date_of_birth
  gender (ENUM: Male/Female/Other)
  phone_number
  email (UNIQUE)
  address
  ssc_gpa (0.00-5.00)
  hsc_gpa (0.00-5.00)
  created_at, updated_at
  ```

#### applicant_login
- Manages user authentication
- Fields:
  ```sql
  login_id (Primary Key)
  email (Foreign Key → applicant_info.email)
  password_hash (SHA2 encrypted)
  last_login
  created_at, updated_at
  ```

### 2. Exam Management

#### exam_center
- Stores examination venue information
- Fields:
  ```sql
  center_id (Primary Key)
  center_name
  center_address
  ```

#### exam_units
- Manages different examination units
- Fields:
  ```sql
  unit_id (Primary Key)
  unit_code
  center_id (Foreign Key → exam_center.center_id)
  exam_date
  exam_time
  exam_duration (default: 60 minutes)
  ```

### 3. Admission Process

#### admit_card
- Generates admission tickets
- Fields:
  ```sql
  exam_roll (Primary Key)
  applicant_id (Foreign Key → applicant_info.applicant_id)
  unit_id (Foreign Key → exam_units.unit_id)
  room_no
  applicant_photo (BLOB)
  issued_at
  ```

#### payment
- Tracks application fees
- Fields:
  ```sql
  payment_id (Primary Key)
  applicant_id (Foreign Key)
  fee_amount
  payment_datetime
  payment_status (ENUM: Paid/Pending/Failed)
  created_at
  ```

#### result
- Records examination results
- Fields:
  ```sql
  result_id (Primary Key)
  applicant_id (Foreign Key)
  unit_id (Foreign Key)
  total_marks (default: 80)
  marks_obtained (0.00-80.00)
  status (ENUM: Passed/Failed/Pending)
  result_published
  ```

## Key Features

### 1. Data Integrity
- Foreign key constraints ensure referential integrity
- Check constraints on GPA values (0.00-5.00)
- Unique email addresses
- Automatic timestamp updates

### 2. Security
- Password hashing using SHA2
- Login tracking
- Secure payment status tracking

### 3. Dashboard View
```sql
CREATE OR REPLACE VIEW applicant_dashboard AS
SELECT
    applicant details,
    unit information,
    marks,
    merit position
FROM multiple tables;
```

## Sample Data Structure

### 1. Applicant Registration
```sql
INSERT INTO applicant_info 
VALUES (
    'Nahid', 'Islam',
    '2006-01-20',
    'Male',
    '01824900698',
    'nahid@gmail.com',
    'Khejurtek, Savar, Dhaka',
    5.00, 4.92
);
```

### 2. Exam Center Setup
```sql
INSERT INTO exam_center 
VALUES ('CSE', 'CSE_DEPT');
```

### 3. Unit Assignment
```sql
INSERT INTO exam_units 
VALUES (
    'A', 1,
    '2024-02-01',
    '10:00:00'
);
```

## Database Relationships

### One-to-One
- applicant_info ↔ applicant_login (via email)

### One-to-Many
- exam_center → exam_units
- applicant_info → payment
- applicant_info → result

### Many-to-One
- admit_card → applicant_info
- admit_card → exam_units

## Data Flow

1. Applicant Registration
   - Create applicant_info entry
   - Generate login credentials
   
2. Payment Processing
   - Record payment attempt
   - Update payment status
   
3. Exam Assignment
   - Create admit card
   - Assign exam center and unit
   
4. Result Processing
   - Record marks
   - Calculate merit position
   - Update status

## Best Practices Implemented

1. Normalization
   - Tables are in 3NF
   - Minimal data redundancy
   - Efficient data organization

2. Data Validation
   - GPA range checks
   - Status enumerations
   - Mandatory field constraints

3. Automated Features
   - Timestamp management
   - Auto-incrementing IDs
   - Default values

4. Performance
   - Indexed primary keys
   - Optimized view for dashboard
   - Efficient joins

## Maintenance Guidelines

1. Regular Backups
   - Daily database dumps
   - Transaction logs

2. Data Cleanup
   - Archive old records
   - Clean temporary data
   - Maintain audit logs

3. Performance Monitoring
   - Index optimization
   - Query performance
   - Storage management

## Security Measures

1. Authentication
   - Hashed passwords
   - Login tracking
   - Session management

2. Data Protection
   - Encrypted sensitive data
   - Access control
   - Audit trails

## Future Enhancements

1. Additional Features
   - Online payment integration
   - Document upload system
   - SMS notification

2. Scalability
   - Partition large tables
   - Archive old data
   - Optimize queries

3. Reporting
   - Advanced analytics
   - Custom reports
   - Performance metrics

This documentation provides a comprehensive overview of the university admission database system, its structure, and functionality.
