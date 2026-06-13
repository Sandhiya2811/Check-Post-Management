# Check-Post-Management

# 🚔 SecureCheck: A Python-SQL Digital Ledger for Police Post Logs

## 📌 Project Title
SecureCheck: A Python-SQL Digital Ledger for Police Post Logs

---

## 🛠️ Skills Take Away From This Project
- Python  
- SQL (PostgreSQL / MySQL / SQLite)  
- Streamlit  
- Data Preprocessing  
- Data Analysis  

---

## 🏢 Domain
- Law Enforcement & Public Safety  
- Real-time Monitoring Systems  

---

## ❗ Problem Statement
Police check posts require a centralized system for logging, tracking, and analyzing vehicle movements.  
Currently, manual logging and inefficient databases slow down security processes.  

This project builds an **SQL-based check post database with a Python-powered dashboard** for real-time insights and alerts.

---

## 💡 Business Use Cases
- Real-time logging of vehicles and personnel  
- Automated suspect vehicle identification using SQL queries  
- Check post efficiency monitoring through data analytics  
- Crime pattern analysis using Python scripts  
- Centralized database for multi-location check posts  

---

## 🧠 Approach

### 1️⃣ Data Collection & Storage
- Define SQL schema for police stop records  
- Store data in PostgreSQL / MySQL  
- Use Python (`pandas`, `sqlalchemy`) to insert and query data  

---

### 2️⃣ Python for Data Processing
- Remove columns containing only missing values  
- Handle missing (NaN) values  
- Clean and preprocess dataset  

---

### 3️⃣ Database Design (SQL)
- Create tables for traffic stop records  
- Insert cleaned data into SQL database  

---

### 4️⃣ Streamlit Dashboard
- Display vehicle logs, violations, and officer reports  
- SQL-based search filters for quick lookup  
- Generate analytics and trends (e.g., high-risk vehicles)  

---

## 📊 Example Scenario
🚗 A 27-year-old male driver was stopped for **Speeding at 2:30 PM**.  
No search was conducted, and he received a citation.  
The stop lasted **6–15 minutes** and was not drug-related.

---

## 📈 Results
- Faster check post operations using SQL queries  
- Automated alerts for flagged vehicles  
- Real-time reporting of security violations  
- Data-driven decision-making for law enforcement  

---

## 📏 Project Evaluation Metrics
- Query Execution Time (optimized SQL performance)  
- Data Accuracy (correct logs and reports)  
- System Uptime (real-time updates without lag)  
- User Engagement (officer interaction with system)  
- Violation Detection Rate  

---

## 🧰 Technical Tags
- Python  
- Data Preprocessing  
- SQL (PostgreSQL / MySQL / SQLite)  
- Streamlit Dashboard  

---

## 🧾 SQL QUERIES

### 🚗 Vehicle-Based
- Top 10 vehicle numbers involved in drug-related stops  
- Most frequently searched vehicles  

---

### 🧍 Demographic-Based
- Age group with highest arrest rate  
- Gender distribution of drivers by country  
- Race & gender combination with highest search rate  

---

### 🕒 Time & Duration Based
- Time of day with most traffic stops  
- Average stop duration by violation  
- Night stops vs arrest probability  

---

### ⚖️ Violation-Based
- Violations most associated with searches/arrests  
- Most common violations among drivers under 25  
- Violations rarely leading to search/arrest  

---

### 🌍 Location-Based
- Countries with highest drug-related stops  
- Arrest rate by country and violation  
- Country with most searches conducted  

---

## 🔥 Complex SQL Queries
1. Yearly breakdown of stops & arrests by country (Subquery + Window Functions)  
2. Driver violation trends based on age and race (Joins + Subquery)  
3. Time period analysis (Year, Month, Hour aggregation)  
4. Violations with high search & arrest rates (Window Functions)  
5. Driver demographics by country (Age, Gender, Race)  
6. Top 5 violations with highest arrest rates  

---

## 📂 Dataset
**Traffic Stops Dataset**

### Dataset Columns:
- stop_date → Date of stop  
- stop_time → Time of stop  
- country_name → Location of stop  
- driver_gender → Gender of driver  
- driver_age_raw → Original age value  
- driver_age → Cleaned age  
- driver_race → Race/ethnicity  
- violation_raw → Original violation reason  
- violation → Cleaned violation type  
- search_conducted → True/False  
- search_type → Type of search  
- stop_outcome → Warning / Citation / Arrest  
- is_arrested → True/False  
- stop_duration → Duration of stop  
- drugs_related_stop → True/False  

---

## 📦 Project Deliverables
- SQL Database Schema (PostgreSQL / MySQL)  
- Python Scripts for Data Processing  
- Streamlit Dashboard for Check Post Management  

---

## 🚀 Conclusion
This project helps improve law enforcement efficiency by combining **Python, SQL, and Streamlit** to create a real-time digital check post monitoring system.

--- 

## 👩‍💻 Author 
**Sandhiya** 

--- 

## ⭐ Support If you like this project, give it a ⭐ on GitHub!
