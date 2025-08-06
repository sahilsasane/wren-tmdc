import psycopg2

conn = psycopg2.connect(
    dbname="defaultdb",
    user="avnadmin",
    password="AVNS_i-uaSubK4DgzTdErWVu",
    host="pg-38af2eba-student-3692.d.aivencloud.com",
    port="19247",
    sslmode="require",
)

cur = conn.cursor()

cur.execute("""
INSERT INTO departments (department_name) VALUES
('Human Resources'), ('Engineering'), ('Finance'), ('Marketing');

INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, department_id, salary) VALUES
('Alice', 'Smith', 'alice.smith@example.com', '555-0101', '2022-01-15', 'HR Manager', 1, 75000),
('Bob', 'Jones', 'bob.jones@example.com', '555-0102', '2023-03-10', 'Software Engineer', 2, 95000),
('Carol', 'White', 'carol.white@example.com', '555-0103', '2021-07-23', 'Marketing Lead', 4, 70000);

INSERT INTO attendance (emp_id, date, status) VALUES
(1, '2025-08-01', 'Present'),
(2, '2025-08-01', 'Absent'),
(3, '2025-08-01', 'Present'),
(1, '2025-08-02', 'Leave');

INSERT INTO salaries (emp_id, month, year, base_salary, bonus, deductions) VALUES
(1, 'July', 2025, 75000, 2000, 500),
(2, 'July', 2025, 95000, 3000, 800),
(3, 'July', 2025, 70000, 1000, 400);
""")

conn.commit()
print("Tables created successfully.")
cur.close()
conn.close()
