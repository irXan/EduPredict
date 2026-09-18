
CREATE DATABASE IF NOT EXISTS edupredict;
USE edupredict;

CREATE TABLE IF NOT EXISTS students_raw (
    student_id STRING,
    course_id STRING,
    term STRING,
    gpa DOUBLE,
    attendance_rate DOUBLE,
    engagement_index DOUBLE,
    midterm_score DOUBLE,
    assignment_score DOUBLE,
    avg_quiz_score DOUBLE,
    lms_logins_per_week INT
) STORED AS PARQUET;

CREATE TABLE IF NOT EXISTS students_partitioned (
    student_id STRING,
    course_id STRING,
    gpa DOUBLE,
    attendance_rate DOUBLE,
    engagement_index DOUBLE,
    midterm_score DOUBLE,
    assignment_score DOUBLE,
    avg_quiz_score DOUBLE,
    lms_logins_per_week INT
) PARTITIONED BY (dropout_risk STRING, term STRING) STORED AS PARQUET;

INSERT OVERWRITE TABLE students_partitioned
PARTITION (dropout_risk, term)
SELECT
    student_id, course_id, gpa, attendance_rate, engagement_index,
    midterm_score, assignment_score, avg_quiz_score, lms_logins_per_week,
    dropout_risk, term
FROM students_raw;

SELECT course_id,
       COUNT(*) AS total_enrolled,
       AVG(gpa) AS avg_gpa,
       AVG(attendance_rate) AS avg_attendance
FROM students_partitioned
GROUP BY course_id
ORDER BY total_enrolled DESC;

SELECT dropout_risk, COUNT(*) AS student_count
FROM students_partitioned
GROUP BY dropout_risk;

SELECT course_id, term, COUNT(*) AS enrolled
FROM students_partitioned
GROUP BY course_id, term
ORDER BY course_id, term;
