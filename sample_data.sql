-- =====================================================================
-- Nathan Auto Detail - Sample Data Script
-- =====================================================================
USE nathan_auto_detail;

-- Clear existing data (child → parent to respect FKs)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE AppointmentAddOns;
TRUNCATE TABLE AppointmentServices;
TRUNCATE TABLE Reviews;
TRUNCATE TABLE Payments;
TRUNCATE TABLE Appointments;
TRUNCATE TABLE Vehicles;
TRUNCATE TABLE ServiceAddOns;
TRUNCATE TABLE Services;
TRUNCATE TABLE Inventory;
TRUNCATE TABLE Employees;
TRUNCATE TABLE Customers;
SET FOREIGN_KEY_CHECKS = 1;

-- ==========================
-- Employees
-- ==========================
INSERT INTO Employees (FirstName, LastName, Email, Phone, HireDate, PositionType, Active) VALUES
('Nate','Owner','owner@nateauto.local','5551112222','2023-01-10','Owner', TRUE),
('Alex','Tech','alex@nateauto.local','5553334444','2023-06-01','Detail Technician', TRUE);

-- ==========================
-- Customers
-- ==========================
INSERT INTO Customers (FirstName, LastName, Email, Phone, Address, City, State, ZipCode, JoinDate, ReferralSource) VALUES
('John','Doe','john.doe@example.com','5551234567','123 Elm St','Springfield','IL','62701', CURDATE()-INTERVAL 120 DAY,'Google'),
('Jane','Smith','jane.smith@example.com','5552345678','456 Oak St','Peoria','IL','61614', CURDATE()-INTERVAL 110 DAY,'Yelp'),
('Mike','Johnson','mike.j@example.com','5553456789','789 Maple Rd','Chicago','IL','60616', CURDATE()-INTERVAL 100 DAY,'Friend'),
('Sara','Brown','sara.brown@example.com','5554567890','321 Birch Blvd','Naperville','IL','60540', CURDATE()-INTERVAL 90 DAY,'Drive-by'),
('Chris','Davis','cdavis@example.com','5555678901','654 Cedar Ave','Decatur','IL','62521', CURDATE()-INTERVAL 80 DAY,'Facebook');

-- ==========================
-- Vehicles
-- ==========================
INSERT INTO Vehicles (CustomerID, Make, Model, Year, Color, LicensePlate, VIN, VehicleType, SpecialNotes) VALUES
(1,'Toyota','Camry',2020,'Silver','ABC123','1HGCM82633A123456','sedan',NULL),
(2,'Honda','Civic',2019,'Black','XYZ789','1HGCM82633A654321','sedan',NULL),
(3,'Ford','F-150',2021,'Blue','LMN456','1FTRX18L1WKA12345','truck','Has lift kit'),
(4,'Chevrolet','Malibu',2018,'White','DEF234','1G1ZD5ST4KF123456','sedan',NULL),
(5,'Nissan','Altima',2022,'Red','GHI345','3N1AB7APXHY123456','sedan',NULL);

-- ==========================
-- Services
-- ==========================
INSERT INTO Services (ServiceName, Descriptions, BasePrice, EstimatedTime, Category, Active) VALUES
('Full Detail','Complete interior & exterior detail',150.00,180,'full detail',TRUE),
('Interior Detail','Vacuum, shampoo, interior surfaces',85.00,90,'interior detail',TRUE),
('Exterior Wash','Wash, dry, wax',60.00,45,'exterior wash',TRUE),
('Monthly Maintenance','Maintenance clean',50.00,30,'monthly maintenance detail',TRUE),
('Deluxe Wax','Advanced wax treatment',90.00,60,'wax full detail',TRUE);

-- ==========================
-- AddOns
-- ==========================
INSERT INTO ServiceAddOns (AddOnName, Description, Price, EstimatedAdditionalTime, Active) VALUES
('Tire Shine','Restore tire gloss',10.00,10,TRUE),
('Window Cleaning','Streak-free windows',20.00,15,TRUE),
('Seat Shampoo','Deep clean fabric seats',45.00,40,TRUE);

-- ==========================
-- Appointments
-- ==========================
INSERT INTO Appointments (CustomerID, VehicleID, EmployeeID, AppointmentDate, StartTime, EndTime, Status) VALUES
(1,1,1,CURDATE()-INTERVAL 20 DAY,'09:00:00','10:30:00','completed'),
(2,2,1,CURDATE()-INTERVAL 15 DAY,'11:00:00','12:00:00','completed'),
(3,3,2,CURDATE()-INTERVAL 10 DAY,'08:30:00','10:00:00','completed'),
(4,4,2,CURDATE()-INTERVAL 5  DAY,'13:00:00','14:00:00','completed'),
(5,5,1,CURDATE()+INTERVAL 2  DAY,'15:00:00','16:30:00','scheduled');

-- ==========================
-- AppointmentServices
-- ==========================
INSERT INTO AppointmentServices (AppointmentID, ServiceID, ActualPrice, Notes) VALUES
(1,3,60.00,'Exterior wash'),
(1,5,90.00,'Added deluxe wax'),
(2,2,85.00,'Interior detail'),
(3,1,150.00,'Full detail'),
(4,4,50.00,'Maintenance package');

-- ==========================
-- AppointmentAddOns
-- ==========================
INSERT INTO AppointmentAddOns (AppointmentID, AddOnID, ActualPrice) VALUES
(1,1,10.00),
(2,2,20.00),
(3,3,45.00);

-- ==========================
-- Payments
-- ==========================
INSERT INTO Payments (AppointmentID, Amount, PaymentDate, PaymentMethod, TransactionID, Status) VALUES
(1,150.00,CURDATE()-INTERVAL 20 DAY,'Credit Card','TXN2001','completed'),
(2,100.00,CURDATE()-INTERVAL 15 DAY,'Cash','TXN2002','completed'),
(3,120.00,CURDATE()-INTERVAL 10 DAY,'Credit Card','TXN2003','completed'),
(4,90.00, CURDATE()-INTERVAL 5  DAY,'Debit Card','TXN2004','completed');

-- ==========================
-- Reviews
-- ==========================
INSERT INTO Reviews (AppointmentID, Rating, Comments, DateSubmitted) VALUES
(1,'5','Great wash and wax!',CURDATE()-INTERVAL 19 DAY),
(2,'4','Interior looked sharp',CURDATE()-INTERVAL 14 DAY),
(3,'5','Truck detail was excellent',CURDATE()-INTERVAL 9 DAY),
(4,'3','Average experience',CURDATE()-INTERVAL 4 DAY);

-- ==========================
-- Inventory
-- ==========================
INSERT INTO Inventory (ItemName, Descriptions, Category, CurrentStock, UnitPrice, OrderPoint, VendorInfo, LastRestockDate) VALUES
('Car Wax','Premium wax for detailing','Supplies',25,15.00,10,'ShineCo Distributors',CURDATE()-INTERVAL 30 DAY),
('Shampoo','Interior fabric shampoo','Supplies',40,8.50,15,'CleanIt Wholesale',CURDATE()-INTERVAL 20 DAY),
('Microfiber Towels','Soft lint-free towels','Supplies',100,2.00,30,'AutoSupplies Inc',CURDATE()-INTERVAL 10 DAY);
