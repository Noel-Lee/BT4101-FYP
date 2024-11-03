import requests
import pandas as pd

# Hugging Face API URL and Authorization headers for GPT-2
API_URL = "https://api-inference.huggingface.co/models/openai-community/gpt2"
headers = {"Authorization": "Bearer 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"}

# Define a function to call the GPT-2 API for a job and resume pair
def match_job_to_resume(job_posting, resume):
    # Use the reduced job description and resume
    reduced_job_description = job_posting['Reduced Job Description']
    reduced_resume = resume['Reduced Resume']

    # Create a prompt using the reduced job description and resume
    prompt = f"""Evaluate how well this job posting matches the job-seeker's profile based on skills match, familiarity with tools, relevant experience, and job location.

    Provide the following:
    - Rating: a score from 0 to 10.
    - Explanation: a detailed reason for why the score was given, including which Key Details in the Job Posting match the Job-Seeker Profile.

    Job-Seeker Profile:
    - Category: {resume['Category']}
    - Key Skills: {reduced_resume}
    
    Job Posting:
    - Job Title: {job_posting['Job Title']}
    - Company: {job_posting['Company']}
    - Location: {job_posting['Location']}
    - Key Details: {reduced_job_description}
    """
    
    # Set up the payload for the API request
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 150},
    }
    
    # Send request to GPT-2 model via Hugging Face API
    response = requests.post(API_URL, headers=headers, json=payload)

    # Check for a successful response
    if response.status_code == 200:
        result = response.json()
        output_text = result[0].get('generated_text', 'No output received')
        
        # Extract rating and explanation from the output
        try:
            # Extract rating as the first number between 0-10
            rating = float([int(s) for s in output_text.split() if s.isdigit() and 0 <= int(s) <= 10][0])
            # Extract explanation by splitting on "Explanation:"
            explanation = output_text.split("Explanation:", 1)[1].strip()
        except (ValueError, IndexError):
            rating = None
            explanation = output_text

        return rating, explanation  # Return rating and explanation
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, "API request failed"
    
# Load datasets
resume_df = pd.read_csv("resume_with_ner.csv")
job_postings_df = pd.read_csv("job_postings_with_ner.csv")

# Iterate through the first 20 resumes only with NER-processed descriptions
top_results = []
for _, resume_row in resume_df.head(20).iterrows():
    # Randomly select 30 job postings for each resume
    sampled_job_postings = job_postings_df.sample(n=20, random_state=42)
    
    ranked_postings = []  # To store job postings with scores for each resume
    for _, job_posting_row in sampled_job_postings.iterrows():
        # Get rating and explanation
        rating, explanation = match_job_to_resume(job_posting_row, resume_row)
        if rating is not None:
            ranked_postings.append({
                "Job Seeker ID": resume_row['ID'],  # Include the job seeker ID
                "Job Title": job_posting_row['Job Title'],
                "Company": job_posting_row['Company'],
                "Job-Seeker Category": resume_row['Category'],
                "Match Rating": rating,
                "Explanation": explanation
            })
    
    # Sort postings by rating in descending order and keep the top 3
    top_ranked = sorted(ranked_postings, key=lambda x: x["Match Rating"], reverse=True)[:3]
    top_results.extend(top_ranked)  # Add to final results

# Save top results to CSV
results_df = pd.DataFrame(top_results)
output_csv_path = "(GPT2)_top_5_job_matches.csv"
results_df.to_csv(output_csv_path, index=False)
print(f"Top 5 job matches for each resume saved to {output_csv_path}")
