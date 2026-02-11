import sys
import os
import uuid
from datetime import datetime
from app.db.session import SessionLocal
from app.models.response_pool import ResponsePool

def seed_responses():
    db = SessionLocal()
    try:
        # Check if already seeded to avoid duplicates
        count = db.query(ResponsePool).count()
        if count > 0:
            print(f"Response pool already has {count} items. Skipping seed.")
            return

        print("Seeding Response Pool...")
        
        responses = [
            {
                "question": "Describe your traffic sources",
                "answer": "Our primary traffic sources are SEO-optimized content marketing, a 50k+ subscriber email newsletter, and targeted Google Ads campaigns in the B2B niche.",
                "category": "Traffic",
                "relevance_score": 0.95
            },
            {
                "question": "How do you plan to promote our product?",
                "answer": "We plan to create in-depth review articles, comparison guides vs competitors, and feature your product in our 'Best Tools of 2024' listicle. We also run webinars where we can demo your solution live.",
                "category": "Promotion",
                "relevance_score": 0.92
            },
            {
                "question": "What is your website URL?",
                "answer": "https://www.automatedonlineprofits.com",
                "category": "General",
                "relevance_score": 0.98
            },
             {
                "question": "What is your monthly audience size?",
                "answer": "We currently have 150,000 monthly unique visitors and 250,000 pageviews, with a 40% growth rate YoY.",
                "category": "Metrics",
                "relevance_score": 0.88
            }
        ]
        
        for r in responses:
            item = ResponsePool(
                id=uuid.uuid4(),
                question=r["question"],
                answer=r["answer"],
                category=r["category"],
                relevance_score=r["relevance_score"],
                embedding=[], # vector support not enabled yet
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(item)
            
        db.commit()
        print(f"✓ Successfully seeded {len(responses)} response items.")
        
    except Exception as e:
        print(f"Error seeding responses: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_responses()
