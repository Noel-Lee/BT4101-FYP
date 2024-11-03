This repository contains a job recommender system designed to enhance job-skills matching through web scraping, NLP, and machine learning. The system ranks job postings based on candidate profiles for personalized recommendations, balancing efficiency and interpretability.

**Features**
Web Scraping: Collects job postings from online job portals.
Skill Extraction with NLP: Uses Named Entity Recognition (NER) to identify skills and relevant entities.
Using smaller LLM model for ranking of top N jobs with each job-seeker's resume

**Future Developments**
Multi-Layered Recommender: Combines smaller models for initial ranking and larger models (e.g., LLaMa 2) for refined, explainable recommendations.
Content-Based Filtering for efficient initial ranking.
User-Labeled Data for evaluation and iterative improvement.

Credits:
Credits to Eben001 for IndeedJobScraper tool. Modified it to include scraping for Salary and Job Description.
