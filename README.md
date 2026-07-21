# DishDash — Data-Driven Restaurant Discovery Platform

DishDash is a hyperlocal restaurant discovery platform that goes beyond traditional ratings by combining price, nutrition, popularity, and location data into a single intelligent score.

Built as part of TECH-UB.0024 — Projects in Programming & Data Science (NYU Stern, Spring 2026).

---

## Live App

https://dishdash.streamlit.app

---

## Overview

Most restaurant apps only show ratings and price, leaving users without deeper insights such as:

- Which restaurants are healthy and affordable?
- What cuisines nearby have the best nutrition profiles?
- Where can users find the best balance between quality, cost, and health?

DishDash addresses this by aggregating multiple datasets and generating a composite metric called the DishDash Score.

### DishDash Score

A unified score that ranks restaurants based on:

- Popularity (ratings and reviews)
- Price level
- Nutritional value
- Location relevance

---

## Key Features

- Smart search for restaurants based on user preferences  
- Interactive map for geographic exploration  
- Analytics dashboard for cuisine and neighborhood trends  
- Natural language recommender  
- Real-time data integration  

---

## Tech Stack

### Frontend
- Streamlit  
- Python  

### Backend and Data Pipeline
- Python  
- SQLite  
- APIs:
  - OpenStreetMap (OSM)  
  - Google Places API  
  - Open Food Facts (OFF)  
  - Hugging Face  

### Data Science
- Clustering  
- Regression analysis  
- Feature engineering  
- Multi-source data fusion  

---

## How It Works

1. Data Collection  
   Restaurant data is pulled from multiple APIs  

2. Data Cleaning and Merging  
   Fuzzy matching is used to combine datasets  

3. Feature Engineering  
   Extract price, nutrition, and rating features  

4. Score Calculation  
   Compute the DishDash Score  

5. Frontend Display  
   Results are visualized using a Streamlit app  

---

## Project Structure

DishDash/
│
├── data/
├── database/
├── notebooks/
├── app/
├── utils/
├── models/
└── README.md

---

## Core Components

### Data Pipeline
- API ingestion  
- Data normalization  
- Fuzzy geographic merging  

### Scoring Engine
- Weighted scoring system combining:
  - Ratings  
  - Price  
  - Nutrition  
  - Distance  

### Analytics Module
- Cuisine clustering  
- Regression insights  
- Trend analysis  

---

## Team — 

| Member    | Contributions |
|----------|--------------|
| Yuri     | Backend pipeline, API integration, database design |
| Allen    | Frontend, scoring engine, Streamlit app |
| Jonathan | Data pipeline testing, analytics, modeling |
| Harry    | UI polish, presentation, demo |

---

## Installation and Setup

```bash
# Clone repository
git clone https://github.com/your-repo/dishdash.git
cd dishdash

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py

---

Example Queries
"Healthy cheap food near me"
"Best-rated Italian restaurants under $15"
"High protein meals near NYU"


```
Future Improvements
Personalized recommendations
User accounts and saved preferences
Mobile application
Real-time crowd data
Expanded geographic coverage
License
MIT License (update if needed)
Acknowledgments
OpenStreetMap
Google Places API
Open Food Facts
Hugging Face
