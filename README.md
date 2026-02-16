 AI-Powered Skincare E-Commerce Platform

A full-stack Flask-based e-commerce web application that provides AI-powered skincare product recommendations, secure Stripe payments, user authentication, and automated email confirmations.

 Features

 User Authentication

Registration, Login, Logout

Secure session management using Flask-Login

AI-Powered Skincare Recommendations

Personalized recommendations using OpenAI API

Based on skin type, concerns, and ingredient preferences

 E-Commerce Functionality

Product listing with pagination

Search functionality

Database-driven product management using SQLAlchemy ORM

Secure Stripe Payment Integration

Stripe Checkout session

Automated order creation after successful payment

 Email Confirmation System

Order confirmation emails using Flask-Mail

Secure credential handling using environment variables (.env)

 Tech Stack

Backend: Flask

Database: SQLAlchemy ORM

Authentication: Flask-Login

AI Integration: OpenAI API

Payments: Stripe

Email Service: Flask-Mail

Environment Management: python-dotenv

Project Structure (Simplified)
SmartTask_Manager/
│
├── app.py
├── templates/
├── static/
├── migrations/
├── .gitignore
├── README.md

 Setup Instructions
1️⃣ Clone the repository
git clone https://github.com/prajukta-panda/SmartTask_Manager.git
cd SmartTask_Manager

2️⃣ Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

4️⃣ Configure Environment Variables

Create a .env file in the root directory and add:

SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_key
STRIPE_SECRET_KEY=your_stripe_key
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_app_password


 Email requires Gmail App Password (2-Step Verification must be enabled).

5️⃣ Run database migrations
flask db upgrade

6️⃣ Run the application
python app.py

Security Note

Sensitive credentials such as API keys and email passwords are stored using environment variables and are excluded from version control via .gitignore.

Learning Outcomes

Built a complete authentication & session system

Integrated third-party APIs (OpenAI & Stripe)

Implemented secure payment workflows

Managed database relationships using ORM

Configured environment-based secure deployments
Author
Prajukta Panda
Backend Developer | Python | Flask | Rest API

