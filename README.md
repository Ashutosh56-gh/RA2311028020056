# 🚀 Backend Microservices Project

## 📌 Overview
This project implements a backend system consisting of multiple components including logging middleware, a vehicle maintenance scheduler, and a notification service. The goal is to design a clean, modular backend architecture with proper API handling and system design considerations.

---

## 📁 Project Structure

. ├── logging_middleware/ ├── vehicle_maintenance_scheduler/ ├── notification_app_be/ ├── notification_system_design.md ├── server.js ├── package.json └── .gitignore

---

## ⚙️ Features

### 🔹 Logging Middleware
- Captures incoming API requests
- Logs request method, route, and response time
- Sends logs to an external logging service

---

### 🚗 Vehicle Maintenance Scheduler
- Processes vehicle service tasks
- Optimizes scheduling based on constraints (time vs impact)
- Uses efficient algorithmic approach for decision making

---

### 🔔 Notification Service
- Fetches notifications from external API
- Prioritizes notifications based on type and recency
- Returns top important notifications

---

## 🧠 System Design
Detailed design decisions, architecture, and scaling strategies are documented in:

👉 notification_system_design.md

---

## 🚀 Getting Started

### 1. Install dependencies
npm install

### 2. Run server
node server.js

Server will start on:
http://localhost:3000

---

## 🧪 API Endpoints

### Vehicle Scheduler
GET /vehicle/schedule

### Notifications
GET /notification/top

---

## 📸 Testing
- APIs tested using Postman
- Includes request, response, and response time validation

---

## 🛠️ Tech Stack
- Node.js
- Express.js
- Axios

---

## 📌 Notes
- Modular folder structure for scalability
- Clean and readable code organization
- Focus on backend logic and system design

---

## ✅ Conclusion
This project demonstrates backend development skills including API design, middleware implementation, algorithmic problem solving, and system architecture planning
