import argparse
import os

import numpy as np
import pandas as pd


def generate_data(n: int, seed: int, output_path: str):
    np.random.seed(seed)
    
    # 1. GPA: Normal(3.2, 0.5), clipped [2.0, 4.0]
    gpa = np.random.normal(3.2, 0.5, n)
    gpa = np.clip(gpa, 2.0, 4.0)
    
    # 2. IELTS: Normal(6.8, 0.7), clipped [4.5, 9.0]
    ielts_score = np.random.normal(6.8, 0.7, n)
    ielts_score = np.clip(ielts_score, 4.5, 9.0)
    
    # 3. Research: correlated with GPA
    # correlation roughly 0.6
    # gpa is in [2,4]. Let's normalize it to [0,1]
    gpa_norm = (gpa - 2.0) / 2.0
    research_base = gpa_norm * 0.6 + np.random.normal(0, 0.2, n) * 0.4
    research_score = np.clip(research_base * 10, 0, 10).round(1)
    
    # 4. Volunteer: Uniform(0, 5)
    volunteer_score = np.random.uniform(0, 5, n).round(1)
    
    # 5. ProgMatch: Bernoulli(0.3) * Uniform(0.5, 1.0)
    is_match = np.random.binomial(1, 0.3, n)
    match_score = is_match * np.random.uniform(0.5, 1.0, n)
    program_match_score = np.clip(match_score * 10, 0, 10).round(1)
    
    # Normalize features for success prob calculation
    # Weights: 0.35 * gpa_norm + 0.25 * (research/10) + 0.20 * (ielts/9) + 0.20 * (match/10)
    ielts_norm = ielts_score / 9.0
    res_norm = research_score / 10.0
    match_norm = program_match_score / 10.0
    
    success_prob = (
        0.35 * gpa_norm +
        0.25 * res_norm +
        0.20 * ielts_norm +
        0.20 * match_norm
    )
    
    # Add a little noise to probabilities
    success_prob = np.clip(success_prob + np.random.normal(0, 0.05, n), 0.01, 0.99)
    
    # Label: Bernoulli(success_prob)
    label = np.random.binomial(1, success_prob)
    
    df = pd.DataFrame({
        "gpa": gpa.round(2),
        "ielts_score": ielts_score.round(1),
        "research_score": research_score,
        "volunteer_score": volunteer_score,
        "program_match_score": program_match_score,
        "success_prob": success_prob.round(3),
        "success": label
    })
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated {n} records with seed {seed} at {output_path}")
    print(df["success"].value_counts(normalize=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic admission records.")
    parser.add_argument("--n", type=int, default=5000, help="Number of records")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, required=True, help="Output CSV path")
    args = parser.parse_args()
    
    generate_data(args.n, args.seed, args.output)
