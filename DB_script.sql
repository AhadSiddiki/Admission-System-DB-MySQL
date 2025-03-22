-- Ahad Siddiki - 371 - JU
-- Create the database schema
DROP DATABASE IF EXISTS uni_admission_371;
CREATE DATABASE IF NOT EXISTS uni_admission_371;
USE uni_admission_371;

-- Table: applicant_info (storing basic applicant info)
CREATE TABLE IF NOT EXISTS applicant_info (
    applicant_id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE DEFAULT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    phone_number VARCHAR(15) DEFAULT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    address TEXT,
    ssc_gpa FLOAT CHECK (ssc_gpa BETWEEN 0.00 AND 5.00),
    hsc_gpa FLOAT CHECK (hsc_gpa BETWEEN 0.00 AND 5.00),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (applicant_id)
);

-- Table: applicant_login (storing login credentials)
CREATE TABLE IF NOT EXISTS applicant_login (
    login_id INT NOT NULL AUTO_INCREMENT,
    email VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    last_login DATETIME DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (login_id),
    FOREIGN KEY (email) REFERENCES applicant_info(email) ON DELETE CASCADE
);

-- Table: exam_center (storing exam center information)
CREATE TABLE IF NOT EXISTS exam_center (
    center_id INT NOT NULL AUTO_INCREMENT,
    center_name VARCHAR(100) NOT NULL,
    center_address TEXT NOT NULL,
    PRIMARY KEY (center_id)
);

-- Table: exam_units (storing exam units details)
CREATE TABLE IF NOT EXISTS exam_units (
    unit_id INT NOT NULL AUTO_INCREMENT,
    unit_code VARCHAR(10) NOT NULL,
    center_id INT NOT NULL,
    exam_date DATE NOT NULL,
    exam_time TIME NOT NULL,
    exam_duration INT DEFAULT 60, -- Duration in minutes
    PRIMARY KEY (unit_id),
    FOREIGN KEY (center_id) REFERENCES exam_center(center_id) ON DELETE CASCADE
);

-- Table: admit_card (storing admit card information)
CREATE TABLE IF NOT EXISTS admit_card (
    exam_roll INT NOT NULL,
    applicant_id INT NOT NULL,
    unit_id INT NOT NULL,
    room_no INT DEFAULT NULL,
    applicant_photo BLOB DEFAULT NULL,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (exam_roll),
    FOREIGN KEY (applicant_id) REFERENCES applicant_info(applicant_id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES exam_units(unit_id) ON DELETE CASCADE
);

-- Table: payment (storing payment details)
CREATE TABLE IF NOT EXISTS payment (
    payment_id INT NOT NULL AUTO_INCREMENT,
    applicant_id INT NOT NULL,
    fee_amount DECIMAL(10, 2) NOT NULL,
    payment_datetime DATETIME DEFAULT NULL,
    payment_status ENUM('Paid', 'Pending', 'Failed') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_id),
    FOREIGN KEY (applicant_id) REFERENCES applicant_info(applicant_id) ON DELETE CASCADE
);

-- Table: result (storing exam results)
CREATE TABLE IF NOT EXISTS result (
    result_id INT NOT NULL AUTO_INCREMENT,
    applicant_id INT NOT NULL,
    unit_id INT NOT NULL,
    total_marks INT DEFAULT 80,
    marks_obtained FLOAT DEFAULT NULL CHECK (marks_obtained BETWEEN 0.00 AND 80.0),
    status ENUM('Passed', 'Failed', 'Pending') DEFAULT 'Pending',
    result_published TIMESTAMP DEFAULT NULL,
    PRIMARY KEY (result_id),
    FOREIGN KEY (applicant_id) REFERENCES applicant_info(applicant_id) ON DELETE CASCADE,
    FOREIGN KEY (unit_id) REFERENCES exam_units(unit_id) ON DELETE CASCADE
);

-- ================================================================
-- Sample Data Insertion (For Testing Purpose)
-- ================================================================

-- Sample applicant registration and login
-- ================================================================

-- Inserting data for applicant_info
INSERT INTO applicant_info (first_name, last_name, date_of_birth, gender, phone_number, email, address, ssc_gpa, hsc_gpa)
VALUES
('Nahid', 'Islam', '2006-01-20', 'Male', '01824900698', 'nahid@gmail.com', 'Khejurtek, Savar, Dhaka', 5.00, 4.92),
('Kayes', 'Mahmud', '2006-05-15', 'Male', '01824900099', 'kayes@gmail.com', '22 mile, Savar, Dhaka', 5.00, 5.00),
('Joy', 'Khan', '2005-03-20', 'Male', '01755500698', 'joy@gmail.com', 'Ishardi, Pabna, Rajshahi', 4.55, 5.00),
('Tarek', 'Islam', '2007-09-10', 'Male', '01725500099', 'tarek@gmail.com', 'Mirpur 12, Dhaka', 4.50, 5.00),
('Shahed', 'Alom', '2006-10-20', 'Male', '01887400698', 'shahed@gmail.com', 'Sadapathor, Volaganj, Shylet', 4.88, 5.00),
('Jesan', 'Islam', '2007-01-05', 'Male', '01843844498', 'jesan@gmail.com', 'Chandanaish, Chittagong', 5.00, 5.00),
('Khaled', 'Mahmud', '2006-05-15', 'Male', '01877777099', 'khaled@gmail.com', 'Jamgora, Ashulia, Dhaka', 3.92, 4.90);

-- Sample login credentials for applicant_login (storing hashed passwords)
INSERT INTO applicant_login (email, password_hash)
VALUES
('nahid@gmail.com', SHA2('nahid', 256)),
('kayes@gmail.com', SHA2('kayes', 256)),
('joy@gmail.com', SHA2('joy', 256)),
('tarek@gmail.com', SHA2('tarek', 256)),
('shahed@gmail.com', SHA2('shahed', 256)),
('jesan@gmail.com', SHA2('jesan', 256)),
('khaled@gmail.com', SHA2('khaled', 256));

-- Sample exam centers data
INSERT INTO exam_center (center_name, center_address)
VALUES
('CSE', 'CSE_DEPT'),
('BOTANY', 'BIOLOGICAL_FACULTY');

-- Sample exam units data (connects to exam center)
INSERT INTO exam_units (unit_code, center_id, exam_date, exam_time)
VALUES
('A', 1, '2024-02-01', '10:00:00'),
('B', 2, '2024-02-02', '11:00:00');

-- Sample admit card data (connects to applicants and exam units)
INSERT INTO admit_card (exam_roll, applicant_id, unit_id, room_no)
VALUES
(220431, 1, 1, 101),
(220432, 2, 2, 102);

-- Sample payment data
INSERT INTO payment (applicant_id, fee_amount, payment_datetime, payment_status)
VALUES
(1, 500.00, '2024-01-20 12:00:00', 'Paid'),
(2, 500.00, '2024-01-21 12:00:00', 'Pending');

-- Sample result data (exam results)
INSERT INTO result (applicant_id, unit_id, marks_obtained, status)
VALUES
(1, 1, 75.5, 'Passed'),
(2, 2, 60.0, 'Passed'),
(3, 1, 57.0, 'Passed'),
(4, 1, 63.0, 'Passed'),
(5, 1, 72.75, 'Passed'),
(6, 1, 71.25, 'Passed'),
(7, 1, 67.75, 'Passed');

-- ================================================
-- View for Applicant Dashboard
-- ================================================
CREATE OR REPLACE VIEW applicant_dashboard AS
SELECT
    ai.applicant_id,
    ai.first_name,
    ai.last_name,
    ai.ssc_gpa,
    ai.hsc_gpa,
    COALESCE(e.unit_code, 'N/A') AS unit_code, -- Replace NULL unit_code with 'N/A'
    COALESCE(r.marks_obtained, 0) AS marks_obtained, -- If marks_obtained is NULL, replace with 0
    COALESCE(r.status, 'Pending') AS result_status, -- Default to 'Pending' if status is NULL
    CASE
        WHEN r.marks_obtained IS NULL THEN 'N/A' -- If marks are NULL, show 'N/A'
        ELSE DENSE_RANK() OVER (PARTITION BY COALESCE(e.unit_code, 'N/A') ORDER BY r.marks_obtained DESC) -- Otherwise, calculate merit position
    END AS merit_position
FROM applicant_info ai
LEFT JOIN result r ON ai.applicant_id = r.applicant_id
LEFT JOIN exam_units e ON r.unit_id = e.unit_id;