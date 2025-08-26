-- =====================================================================
-- Nathan Auto Detail Management System - Database Schema (MySQL 8+)
-- =====================================================================
-- How to use:
--   CREATE DATABASE IF NOT EXISTS nathan_auto_detail
--     CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
--   USE nathan_auto_detail;
--   Run this script.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS nathan_auto_detail
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE nathan_auto_detail;

-- Safety reset (child -> parent)
SET FOREIGN_KEY_CHECKS = 0;

DROP VIEW IF EXISTS RecentPaymentsSummary;
DROP VIEW IF EXISTS UpcomingAppointments;
DROP VIEW IF EXISTS CurrentCustomers;
DROP VIEW IF EXISTS Top3RatedServices;

DROP TRIGGER IF EXISTS log_deleted_appointments;
DROP TRIGGER IF EXISTS prevent_overbooking;
DROP TRIGGER IF EXISTS validate_phone_insert;
DROP TRIGGER IF EXISTS validate_phone_update;

DROP PROCEDURE IF EXISTS UpdateAppointmentStatus;
DROP PROCEDURE IF EXISTS CustomerAppointmentHistory;
DROP PROCEDURE IF EXISTS SummarizeRecentPayments;

DROP TABLE IF EXISTS AppointmentAddOns;
DROP TABLE IF EXISTS AppointmentServices;
DROP TABLE IF EXISTS Reviews;
DROP TABLE IF EXISTS Payments;
DROP TABLE IF EXISTS Appointments;
DROP TABLE IF EXISTS ServiceAddOns;
DROP TABLE IF EXISTS Services;
DROP TABLE IF EXISTS Vehicles;
DROP TABLE IF EXISTS Employees;
DROP TABLE IF EXISTS Inventory;
DROP TABLE IF EXISTS DeletedAppointmentsLog;
DROP TABLE IF EXISTS Customers;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================
-- Customers
-- =====================
CREATE TABLE Customers (
  CustomerID     INT AUTO_INCREMENT PRIMARY KEY,
  FirstName      VARCHAR(50)  NOT NULL,
  LastName       VARCHAR(50)  NOT NULL,
  Email          VARCHAR(100) NOT NULL,
  Phone          VARCHAR(20)  NOT NULL, -- validated by triggers
  Address        VARCHAR(255),
  City           VARCHAR(50),
  State          VARCHAR(50),
  ZipCode        VARCHAR(10),
  JoinDate       DATE         NOT NULL DEFAULT (CURRENT_DATE),
  ReferralSource VARCHAR(100),
  CONSTRAINT uq_customers_email UNIQUE (Email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- Employees
-- =====================
CREATE TABLE Employees (
  EmployeeID   INT AUTO_INCREMENT PRIMARY KEY,
  FirstName    VARCHAR(50)  NOT NULL,
  LastName     VARCHAR(50)  NOT NULL,
  Email        VARCHAR(100),
  Phone        VARCHAR(20),
  HireDate     DATE,
  PositionType VARCHAR(50),
  Active       BOOLEAN      NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- Vehicles (belongs to Customer)
-- =====================
CREATE TABLE Vehicles (
  VehicleID     INT AUTO_INCREMENT PRIMARY KEY,
  CustomerID    INT          NOT NULL,
  Make          VARCHAR(50)  NOT NULL,
  Model         VARCHAR(50)  NOT NULL,
  Year          INT,
  Color         VARCHAR(30),
  LicensePlate  VARCHAR(20)  NOT NULL,
  VIN           VARCHAR(50),
  VehicleType   ENUM('sedan','SUV','truck'),
  SpecialNotes  TEXT,
  CONSTRAINT fk_vehicles_customer
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT uq_vehicles_plate UNIQUE (LicensePlate),
  CONSTRAINT uq_vehicles_vin   UNIQUE (VIN)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_vehicles_customer ON Vehicles(CustomerID);

-- =====================
-- Services & AddOns
-- =====================
CREATE TABLE Services (
  ServiceID       INT AUTO_INCREMENT PRIMARY KEY,
  ServiceName     VARCHAR(100) NOT NULL,
  Descriptions    TEXT,
  BasePrice       DECIMAL(10,2) NOT NULL,
  EstimatedTime   INT, -- minutes
  Category        ENUM('wax full detail','monthly maintenance detail','full detail','exterior wash','interior detail'),
  Active          BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE ServiceAddOns (
  AddOnID                INT AUTO_INCREMENT PRIMARY KEY,
  AddOnName              VARCHAR(100) NOT NULL,
  Description            TEXT,
  Price                  DECIMAL(10,2) NOT NULL,
  EstimatedAdditionalTime INT, -- minutes
  Active                 BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- Appointments (Customer + Vehicle + optional Employee)
-- =====================
CREATE TABLE Appointments (
  AppointmentID   INT AUTO_INCREMENT PRIMARY KEY,
  CustomerID      INT          NOT NULL,
  VehicleID       INT          NOT NULL,
  EmployeeID      INT          NULL,
  AppointmentDate DATE         NOT NULL,
  StartTime       TIME         NOT NULL,
  EndTime         TIME         NOT NULL,
  Status          ENUM('scheduled','in progress','completed','canceled') NOT NULL DEFAULT 'scheduled',
  CONSTRAINT fk_appts_customer
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_appts_vehicle
    FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_appts_employee
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
    ON UPDATE CASCADE ON DELETE SET NULL,
  CONSTRAINT chk_time_order CHECK (EndTime > StartTime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_appts_customer ON Appointments(CustomerID);
CREATE INDEX idx_appts_vehicle  ON Appointments(VehicleID);
CREATE INDEX idx_appts_date     ON Appointments(AppointmentDate);
CREATE INDEX idx_appts_employee ON Appointments(EmployeeID);

-- =====================
-- AppointmentServices (line items)
-- =====================
CREATE TABLE AppointmentServices (
  AppointmentServiceID INT AUTO_INCREMENT PRIMARY KEY,
  AppointmentID        INT           NOT NULL,
  ServiceID            INT           NOT NULL,
  ActualPrice          DECIMAL(10,2),
  Notes                TEXT,
  CONSTRAINT fk_apptsvcs_appt
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_apptsvcs_service
    FOREIGN KEY (ServiceID) REFERENCES Services(ServiceID)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_appt_service UNIQUE (AppointmentID, ServiceID) -- prevent duplicates
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_apptsvcs_appt   ON AppointmentServices(AppointmentID);
CREATE INDEX idx_apptsvcs_servce ON AppointmentServices(ServiceID);

-- =====================
-- AppointmentAddOns (line items)
-- =====================
CREATE TABLE AppointmentAddOns (
  AppointmentAddOnID INT AUTO_INCREMENT PRIMARY KEY,
  AppointmentID      INT           NOT NULL,
  AddOnID            INT           NOT NULL,
  ActualPrice        DECIMAL(10,2),
  CONSTRAINT fk_apptaddons_appt
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_apptaddons_addon
    FOREIGN KEY (AddOnID) REFERENCES ServiceAddOns(AddOnID)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_appt_addon UNIQUE (AppointmentID, AddOnID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_apptaddons_appt ON AppointmentAddOns(AppointmentID);
CREATE INDEX idx_apptaddons_add  ON AppointmentAddOns(AddOnID);

-- =====================
-- Payments
-- =====================
CREATE TABLE Payments (
  PaymentID      INT AUTO_INCREMENT PRIMARY KEY,
  AppointmentID  INT           NOT NULL,
  Amount         DECIMAL(10,2) NOT NULL,
  PaymentDate    DATE          NOT NULL,
  PaymentMethod  VARCHAR(50)   NOT NULL,
  TransactionID  VARCHAR(100),
  Status         ENUM('pending','completed','refunded') NOT NULL DEFAULT 'completed',
  CONSTRAINT fk_payments_appt
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_payments_appt ON Payments(AppointmentID);
CREATE INDEX idx_payments_date ON Payments(PaymentDate);

-- =====================
-- Inventory (standalone)
-- =====================
CREATE TABLE Inventory (
  ItemID        INT AUTO_INCREMENT PRIMARY KEY,
  ItemName      VARCHAR(100) NOT NULL,
  Descriptions  TEXT,
  Category      VARCHAR(50),
  CurrentStock  INT          NOT NULL DEFAULT 0,
  UnitPrice     DECIMAL(10,2),
  OrderPoint    INT,
  VendorInfo    TEXT,
  LastRestockDate DATE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================
-- Reviews (by Appointment)
-- =====================
CREATE TABLE Reviews (
  ReviewID       INT AUTO_INCREMENT PRIMARY KEY,
  AppointmentID  INT           NOT NULL,
  Rating         ENUM('1','2','3','4','5') NOT NULL,
  Comments       TEXT,
  DateSubmitted  DATE          NOT NULL DEFAULT (CURRENT_DATE),
  CONSTRAINT fk_reviews_appt
    FOREIGN KEY (AppointmentID) REFERENCES Appointments(AppointmentID)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_reviews_appt ON Reviews(AppointmentID);

-- =====================
-- Deleted Appointments Audit Log (for trigger)
-- =====================
CREATE TABLE DeletedAppointmentsLog (
  LogID           INT AUTO_INCREMENT PRIMARY KEY,
  AppointmentID   INT NOT NULL,
  CustomerID      INT NOT NULL,
  VehicleID       INT NOT NULL,
  AppointmentDate DATE,
  StartTime       TIME,
  EndTime         TIME,
  DeletedAt       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------
-- Views
-- -----------------------------------------------------
-- Top 3 Rated Services (min 3 reviews), using numeric cast for AVG
CREATE VIEW Top3RatedServices AS
SELECT
  s.ServiceName,
  AVG(CAST(r.Rating AS UNSIGNED)) AS AvgRating
FROM Reviews r
JOIN Appointments a  ON r.AppointmentID = a.AppointmentID
JOIN AppointmentServices aps ON a.AppointmentID = aps.AppointmentID
JOIN Services s ON aps.ServiceID = s.ServiceID
GROUP BY s.ServiceID
HAVING COUNT(*) >= 3
ORDER BY AvgRating DESC
LIMIT 3;

-- Current Customers (with any scheduled/in progress/completed appts)
CREATE VIEW CurrentCustomers AS
SELECT DISTINCT
  c.CustomerID, c.FirstName, c.LastName, c.Email, c.Phone,
  c.City, c.State, c.JoinDate, c.ReferralSource
FROM Customers c
JOIN Appointments a ON c.CustomerID = a.CustomerID
WHERE a.Status IN ('scheduled','in progress','completed');

-- Upcoming Appointments (simple schedule view)
CREATE VIEW UpcomingAppointments AS
SELECT 
  a.AppointmentID,
  a.AppointmentDate,
  a.StartTime,
  a.EndTime,
  a.Status,
  c.FirstName,
  c.LastName,
  c.Phone,
  v.Make,
  v.Model,
  v.LicensePlate,
  v.VehicleType
FROM Appointments a
JOIN Customers c ON a.CustomerID = c.CustomerID
JOIN Vehicles  v ON a.VehicleID  = v.VehicleID
WHERE a.Status IN ('scheduled','in progress')
ORDER BY a.AppointmentDate, a.StartTime;

-- Recent Payments (last 30 days, completed)
CREATE VIEW RecentPaymentsSummary AS
SELECT
  p.PaymentID,
  p.PaymentDate,
  p.Amount,
  p.PaymentMethod,
  c.FirstName,
  c.LastName,
  a.AppointmentDate
FROM Payments p
JOIN Appointments a ON p.AppointmentID = a.AppointmentID
JOIN Customers   c ON a.CustomerID    = c.CustomerID
WHERE p.Status = 'completed'
  AND p.PaymentDate >= (CURRENT_DATE - INTERVAL 30 DAY)
ORDER BY p.PaymentDate DESC;

-- -----------------------------------------------------
-- Stored Procedures
-- -----------------------------------------------------
DELIMITER //

-- Summarize recent payments (used by GUI Reports)
CREATE PROCEDURE SummarizeRecentPayments(IN days_interval INT)
BEGIN
  SELECT PaymentID, AppointmentID, Amount, PaymentDate
  FROM Payments
  WHERE PaymentDate >= DATE_SUB(CURDATE(), INTERVAL days_interval DAY)
  ORDER BY PaymentDate DESC;
END //

-- Customer appointment history (fix param shadowing)
CREATE PROCEDURE CustomerAppointmentHistory(IN pCustomerID INT)
BEGIN
  SELECT a.AppointmentDate, s.ServiceName, r.Rating, r.Comments
  FROM Appointments a
  JOIN AppointmentServices aps ON a.AppointmentID = aps.AppointmentID
  JOIN Services s             ON aps.ServiceID    = s.ServiceID
  LEFT JOIN Reviews r         ON a.AppointmentID  = r.AppointmentID
  WHERE a.CustomerID = pCustomerID
  ORDER BY a.AppointmentDate DESC;
END //

-- Update appointment status (used by GUI button)
CREATE PROCEDURE UpdateAppointmentStatus(IN pAppointmentID INT, IN pNewStatus VARCHAR(20))
BEGIN 
  UPDATE Appointments
  SET Status = pNewStatus
  WHERE AppointmentID = pAppointmentID;
END //

DELIMITER ;

-- -----------------------------------------------------
-- Triggers
-- -----------------------------------------------------
DELIMITER //

-- Audit deletions of appointments
CREATE TRIGGER log_deleted_appointments
BEFORE DELETE ON Appointments
FOR EACH ROW
BEGIN
  INSERT INTO DeletedAppointmentsLog (
    AppointmentID, CustomerID, VehicleID, AppointmentDate, StartTime, EndTime
  )
  VALUES (OLD.AppointmentID, OLD.CustomerID, OLD.VehicleID, OLD.AppointmentDate, OLD.StartTime, OLD.EndTime);
END //

-- Prevent overlapping appointments per vehicle (same day)
CREATE TRIGGER prevent_overbooking
BEFORE INSERT ON Appointments
FOR EACH ROW
BEGIN
  DECLARE issue_count INT;
  SELECT COUNT(*) INTO issue_count
  FROM Appointments
  WHERE VehicleID = NEW.VehicleID
    AND AppointmentDate = NEW.AppointmentDate
    AND (
          (NEW.StartTime BETWEEN StartTime AND EndTime)
       OR (NEW.EndTime   BETWEEN StartTime AND EndTime)
       OR (StartTime BETWEEN NEW.StartTime AND NEW.EndTime)
        );
  IF issue_count > 0 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Check For Overlapping Appointment Date/Times!';
  END IF;
END //

-- Phone number validation (10 digits, no symbols): INSERT
CREATE TRIGGER validate_phone_insert
BEFORE INSERT ON Customers
FOR EACH ROW
BEGIN
  IF NEW.Phone NOT REGEXP '^[0-9]{10}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Invalid Phone Number: Must be 10 digits | No symbols';
  END IF;
END //

-- Phone number validation: UPDATE
CREATE TRIGGER validate_phone_update
BEFORE UPDATE ON Customers
FOR EACH ROW
BEGIN
  IF NEW.Phone NOT REGEXP '^[0-9]{10}$' THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Invalid Phone Number: Must be 10 digits | No symbols';
  END IF;
END //

DELIMITER ;

-- =======================
-- SAMPLE DATA (your seed)
-- =======================

-- Customers
INSERT INTO Customers (FirstName, LastName, Email, Phone, Address, City, State, ZipCode, JoinDate, ReferralSource) VALUES
('John', 'Doe', 'john.doe@example.com', '5551234567', '123 Elm St', 'Springfield', 'IL', '62701', CURDATE(), 'Google'),
('Jane', 'Smith', 'jane.smith@example.com', '5552345678', '456 Oak St', 'Peoria', 'IL', '61614', CURDATE(), 'Yelp'),
('Mike', 'Johnson', 'mike.j@example.com', '5553456789', '789 Maple Rd', 'Chicago', 'IL', '60616', CURDATE(), 'Friend'),
('Sara', 'Brown', 'sara.brown@example.com', '5554567890', '321 Birch Blvd', 'Naperville', 'IL', '60540', CURDATE(), 'Drive-by'),
('Chris', 'Davis', 'cdavis@example.com', '5555678901', '654 Cedar Ave', 'Decatur', 'IL', '62521', CURDATE(), 'Facebook'),
('Laura', 'Wilson', 'laura.w@example.com', '5556789012', '987 Walnut St', 'Champaign', 'IL', '61820', CURDATE(), 'Instagram'),
('Kevin', 'Anderson', 'kev.anderson@example.com', '5557890123', '159 Ash Ln', 'Rockford', 'IL', '61107', CURDATE(), 'Referral'),
('Tina', 'Martinez', 'tina.m@example.com', '5558901234', '753 Cherry Dr', 'Aurora', 'IL', '60505', CURDATE(), 'Google'),
('Ryan', 'Lee', 'ryan.lee@example.com', '5559012345', '951 Poplar Ct', 'Elgin', 'IL', '60120', CURDATE(), 'Yelp'),
('Emily', 'Clark', 'em.clark@example.com', '5550123456', '864 Fir Cir', 'Joliet', 'IL', '60435', CURDATE(), 'Flyer'),
('Steve', 'Walker', 'steve.w@example.com', '5550987654', '111 Beech Ave', 'Waukegan', 'IL', '60085', CURDATE(), 'Friend'),
('Ashley', 'Young', 'ashley.y@example.com', '5550876543', '222 Spruce St', 'Cicero', 'IL', '60804', CURDATE(), 'Google'),
('Brandon', 'Hall', 'brandon.h@example.com', '5550765432', '333 Dogwood Way', 'Evanston', 'IL', '60201', CURDATE(), 'Instagram'),
('Megan', 'Allen', 'megan.a@example.com', '5550654321', '444 Redwood Rd', 'Skokie', 'IL', '60076', CURDATE(), 'Referral'),
('Justin', 'King', 'justin.k@example.com', '5550543210', '555 Sequoia Dr', 'Berwyn', 'IL', '60402', CURDATE(), 'Drive-by');

-- Employees (minimal)
INSERT INTO Employees (FirstName, LastName, Email, Active) VALUES
('Nate','Owner','owner@nateauto.local', TRUE),
('Alex','Tech','alex@nateauto.local', TRUE);

-- Vehicles
INSERT INTO Vehicles (CustomerID, Make, Model, Year, Color, LicensePlate, VIN, VehicleType, SpecialNotes) VALUES
(1, 'Toyota', 'Camry', 2020, 'Silver', 'ABC123', '1HGCM82633A123456', 'sedan', NULL),
(2, 'Honda', 'Civic', 2018, 'Black', 'XYZ789', '1HGCM82633A654321', 'sedan', NULL),
(3, 'Ford', 'F-150', 2021, 'Blue', 'LMN456', '1FTRX18L1WKA12345', 'truck', 'Has lift kit'),
(4, 'Chevrolet', 'Malibu', 2019, 'White', 'DEF234', '1G1ZD5ST4KF123456', 'sedan', NULL),
(5, 'Nissan', 'Altima', 2022, 'Red', 'GHI345', '3N1AB7APXHY123456', 'sedan', NULL),
(6, 'Jeep', 'Wrangler', 2020, 'Green', 'JKL567', '1C4BJWDG7HL123456', 'SUV', 'Off-road mods'),
(7, 'Subaru', 'Outback', 2019, 'Gray', 'MNO678', '4S4BSANC3K1234567', 'SUV', NULL),
(8, 'BMW', 'X5', 2021, 'Black', 'PQR890', '5UXCR6C56KLL12345', 'SUV', NULL),
(9, 'Honda', 'Civic', 2019, 'Red', 'CIV123', '1HGEM229X1L123456', 'sedan', NULL),
(10, 'Chevy', 'Silverado', 2021, 'Gray', 'SIL321', '3GCEK14X98G123456', 'truck', 'Custom rims'),
(11, 'Tesla', 'Model 3', 2023, 'White', 'TES789', '5YJ3E1EA7KF123456', 'sedan', 'Autopilot enabled'),
(12, 'Kia', 'Sorento', 2020, 'Gray', 'KIA321', '5XYPGDA38LG123456', 'SUV', NULL),
(13, 'Mazda', 'CX-5', 2021, 'Red', 'CX5123', 'JM3KFBDY9M1234567', 'SUV', NULL),
(14, 'Chevy', 'Silverado', 2022, 'Black', 'CHEVY22', '3GCUYDED5MG123456', 'truck', NULL),
(15, 'Ford', 'Escape', 2018, 'White', 'ESC888', '1FMCU0GD9JUA12345', 'SUV', NULL);

-- Services
INSERT INTO Services (ServiceName, Descriptions, BasePrice, EstimatedTime, Category, Active) VALUES
('Full Detail', 'Complete interior and exterior cleaning', 150.00, 180, 'full detail', TRUE),
('Interior Detail', 'Thorough vacuum and shampoo of interior', 85.00, 90, 'interior detail', TRUE),
('Exterior Wash', 'Exterior wash and dry with wax', 60.00, 45, 'exterior wash', TRUE),
('Monthly Maintenance', 'Basic touch-up detail', 50.00, 30, 'monthly maintenance detail', TRUE),
('Deluxe Wax', 'Advanced wax treatment', 90.00, 60, 'wax full detail', TRUE),
('Quick Wash', 'Basic quick exterior wash', 35.00, 20, 'exterior wash', TRUE),
('Engine Bay Detail', 'Clean and detail engine compartment', 40.00, 30, 'exterior wash', TRUE),
('Pet Hair Removal', 'Removes excessive pet hair', 35.00, 30, 'interior detail', TRUE),
('Odor Treatment', 'Neutralizes interior odors', 25.00, 20, 'interior detail', TRUE),
('Clay Bar Treatment', 'Removes surface contaminants', 70.00, 60, 'wax full detail', TRUE),
('Ceramic Coating', 'Durable paint protection', 300.00, 240, 'full detail', TRUE),
('Window Cleaning', 'Streak-free windows', 20.00, 15, 'interior detail', TRUE),
('Tire Shine', 'Restores gloss to tires', 10.00, 10, 'exterior wash', TRUE),
('Seat Shampoo', 'Deep clean fabric seats', 45.00, 40, 'interior detail', TRUE),
('Dashboard Detail', 'Cleans and protects dashboard', 20.00, 15, 'interior detail', TRUE);

-- Appointments
INSERT INTO Appointments (CustomerID, VehicleID, EmployeeID, AppointmentDate, StartTime, EndTime, Status) VALUES
(1, 1, 1, '2024-05-01', '09:00:00', '10:00:00', 'completed'),
(2, 2, 1, '2024-05-02', '10:00:00', '11:00:00', 'completed'),
(3, 3, 2, '2024-05-03', '08:00:00', '09:30:00', 'completed'),
(4, 4, 2, '2024-05-04', '13:00:00', '14:00:00', 'completed'),
(5, 5, 1, '2024-05-05', '15:00:00', '16:00:00', 'completed'),
(6, 6, 2, '2024-05-06', '11:00:00', '12:00:00', 'completed'),
(7, 7, 1, '2024-05-07', '09:30:00', '10:30:00', 'completed'),
(8, 8, 1, '2024-05-08', '12:00:00', '13:00:00', 'completed'),
(9, 9, 2, '2024-05-09', '14:00:00', '15:00:00', 'completed'),
(10, 10, 1, '2024-05-10', '08:30:00', '09:30:00', 'completed'),
(11, 11, 2, '2024-05-11', '10:00:00', '11:30:00', 'completed'),
(12, 12, 2, '2024-05-12', '11:00:00', '12:30:00', 'completed'),
(13, 13, 1, '2024-05-13', '13:00:00', '14:00:00', 'completed'),
(14, 14, 1, '2024-05-14', '14:30:00', '15:30:00', 'completed'),
(15, 15, 2, '2024-05-15', '15:00:00', '16:00:00', 'completed');

-- Payments
INSERT INTO Payments (AppointmentID, Amount, PaymentDate, PaymentMethod, TransactionID, Status) VALUES
(1, 80.00,  CURDATE(), 'Credit Card', 'TXN1001', 'completed'),
(2, 100.00, CURDATE(), 'Cash',        'TXN1002', 'completed'),
(3, 75.50,  CURDATE(), 'Credit Card', 'TXN1003', 'completed'),
(4, 120.00, CURDATE(), 'Debit Card',  'TXN1004', 'completed'),
(5, 90.00,  CURDATE(), 'Credit Card', 'TXN1005', 'completed'),
(6, 60.00,  CURDATE(), 'Cash',        'TXN1006', 'completed'),
(7, 105.25, CURDATE(), 'Credit Card', 'TXN1007', 'completed'),
(8, 130.00, CURDATE(), 'Venmo',       'TXN1008', 'completed'),
(9, 110.75, CURDATE(), 'Credit Card', 'TXN1009', 'completed'),
(10, 99.99, CURDATE(), 'Debit Card',  'TXN1010', 'completed'),
(11, 89.50, CURDATE(), 'Cash',        'TXN1011', 'completed'),
(12, 115.00, CURDATE(), 'Credit Card','TXN1012', 'completed'),
(13, 140.00, CURDATE(), 'Cash',       'TXN1013', 'completed'),
(14, 70.00, CURDATE(), 'Credit Card', 'TXN1014', 'completed'),
(15, 100.00, CURDATE(), 'Cash',       'TXN1015', 'completed');
