# Automated MCQ Generation System

A web-based system that automatically generates multiple-choice questions (MCQs) using large language models.  
The application is designed for exam preparation and assessment practice, with configurable test controls and clean output formatting.

---

## 🚀 Key Features

- Automated MCQ generation using Google Gemini API
- Generates exam-style questions with four options, correct answer, and explanation
- Configurable test controls (number of questions, optional timer)
- Robust parsing logic to convert LLM output into structured quizzes
- Clean Flask-based web interface for interactive use

---

## 🧠 System Overview

- **Flask** handles routing and UI rendering
- **LLM Integration Layer** (`apif.py`)
  - Prompt engineering for structured MCQ generation
  - API-level error handling
- **Parsing Engine**
  - Converts raw LLM output into validated MCQ objects
  - Handles formatting inconsistencies gracefully
- **Frontend**
  - Topic input, quiz rendering, and optional timer support

---

## 📁 Project Structure

Automated-MCQ-Generation-System/

├── app.py # Flask entry point
|
├── apif.py # Gemini API integration & prompt logic
|
├── requirements.txt
|
├── README.md
|
├── templates/ # HTML templates
|
└── static/ 

---

## 🔐 API Key Management

This project uses the Google Gemini API.

- API keys are stored locally using a `.env` file
- The `.env` file is excluded from version control for security reasons

**Note:**  
You must add your own API key to run this project locally.

---

## 🧩 Error Handling & Reliability

- Graceful handling of missing or invalid API keys
- Fallback to raw LLM output display if parsing fails
- Input validation for topic and number of questions
- Parser designed to handle formatting inconsistencies in LLM responses

---

## 🛠️ Tech Stack

- Python
- Flask
- Google Gemini API
- HTML / CSS
- JavaScript (for quiz interaction and timers)

---

## ▶️ Running the Application

```bash
pip install -r requirements.txt
python app.py

