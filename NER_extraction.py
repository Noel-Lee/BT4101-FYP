import spacy
import pandas as pd

# Load SpaCy NER model
nlp = spacy.load("en_core_web_sm")

# Define a function to extract key entities using NER
def extract_key_entities(text):
    doc = nlp(text)
    # Filter entities to include relevant job and skill-related info
    entities = [ent.text for ent in doc.ents if ent.label_ in {"ORG", "GPE", "PERSON", "DATE", "TIME", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL"}]
    return " ".join(entities)  # Join extracted entities into a reduced description

# Load and preprocess job postings dataset
job_postings_df = pd.read_csv("tech_singapore.csv")
job_postings_df['Job Description'] = job_postings_df['Job Description'].fillna('')  # Fill NaN with empty string
job_postings_df['Reduced Job Description'] = job_postings_df['Job Description'].apply(extract_key_entities)

# Save the job_postings_df with NER-processed job descriptions to a CSV file
job_postings_with_ner_path = "job_postings_with_ner.csv"
job_postings_df.to_csv(job_postings_with_ner_path, index=False)
print(f"Job postings with NER-processed descriptions saved to {job_postings_with_ner_path}")

# Define a similar function to reduce the resume descriptions
def extract_resume_entities(text):
    doc = nlp(text)
    # Extract key entities focusing on skills, education, and experiences
    entities = [ent.text for ent in doc.ents if ent.label_ in {"ORG", "GPE", "PERSON", "DATE", "TIME", "MONEY", "QUANTITY", "ORDINAL", "CARDINAL"}]
    return " ".join(entities)

# Load and preprocess resume dataset
resume_df = pd.read_csv("UpdatedResumeDataSetwithID.csv")
resume_df['Resume'] = resume_df['Resume'].fillna('')  # Fill NaN with empty string
resume_df['Reduced Resume'] = resume_df['Resume'].apply(extract_resume_entities)

# Save the resume_df with NER-processed resumes to a CSV file
resume_with_ner_path = "resume_with_ner.csv"
resume_df.to_csv(resume_with_ner_path, index=False)
print(f"Resumes with NER-processed descriptions saved to {resume_with_ner_path}")