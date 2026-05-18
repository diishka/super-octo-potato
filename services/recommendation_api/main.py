from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="Social Movie Recommender API",
    version="0.1.0",
    description="Future home for heavier recommendation logic and experimentation.",
)


class RecommendationEnvelope(BaseModel):
    user_id: int
    status: str
    message: str


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/users/{user_id}/recommendations", response_model=RecommendationEnvelope)
def get_recommendations(user_id: int):
    return RecommendationEnvelope(
        user_id=user_id,
        status="stub",
        message="Recommendation engine can be extracted here when Django-side logic becomes too heavy.",
    )
