import requests
import pandas as pd

# Hugging Face API URL and Authorization headers for BART
API_URL = "https://api-inference.huggingface.co/models/Kaludi/chatgpt-gpt4-prompts-bart-large-cnn-samsum"
headers = {"Authorization": "Bearer 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"}

# Define a function to call the BART API for a job and resume pair
def match_job_to_resume(job_posting, resume):
    # Use the reduced job description and resume
    reduced_job_description = job_posting['Reduced Job Description']
    reduced_resume = resume['Reduced Resume']

    # Create a simplified prompt for BART
    prompt = f"""Summarize how well the following job posting matches the job-seeker's profile based on skills, tools, experience, and location.

    Job-Seeker Profile:
    - Category: {resume['Category']}
    - Skills: {reduced_resume}
    
    Job Posting:
    - Title: {job_posting['Job Title']}
    - Company: {job_posting['Company']}
    - Location: {job_posting['Location']}
    - Details: {reduced_job_description}

    Generate a brief summary of the match."""
    
    # Set up the payload for the API request
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 100},
    }
    
    # Send request to BART model via Hugging Face API
    response = requests.post(API_URL, headers=headers, json=payload)

    # Check for a successful response
    if response.status_code == 200:
        result = response.json()
        output_text = result[0].get('generated_text', 'No output received')
        
        # Debugging: Print the output to see how BART responds
        print(f"Model Output:\n{output_text}\n{'='*50}\n")
        
        # Assuming the model does not provide a structured score, let's manually assign one
        # based on keyword presence or specific terms (for demonstration)
        if "excellent match" in output_text.lower():
            rating = 90
        elif "good match" in output_text.lower():
            rating = 75
        elif "fair match" in output_text.lower():
            rating = 50
        elif "poor match" in output_text.lower():
            rating = 25
        else:
            rating = 0  # Default rating if no clear match is provided
        
        explanation = output_text  # Use the summary as the explanation
        print(f"Rating: {rating}, Explanation: {explanation}")

        return rating, explanation  # Return rating and explanation
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, "API request failed"

# Load datasets
resume_df = pd.read_csv("resume_with_ner.csv")
job_postings_df = pd.read_csv("job_postings_with_ner.csv")

# Iterate through the first three resumes only with NER-processed descriptions
top_results = []
for _, resume_row in resume_df.head(3).iterrows():
    ranked_postings = []  # To store job postings with scores for each resume
    for _, job_posting_row in job_postings_df.iterrows():
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
    
    # Sort postings by rating in descending order and keep the top 5
    top_ranked = sorted(ranked_postings, key=lambda x: x["Match Rating"], reverse=True)[:5]
    top_results.extend(top_ranked)  # Add to final results

# Save top results to CSV
results_df = pd.DataFrame(top_results)
output_csv_path = "(Kaludi_bart_large_cnn_samsum)_top_5_job_matches.csv"
results_df.to_csv(output_csv_path, index=False)
print(f"Top 5 job matches for each resume saved to {output_csv_path}")
