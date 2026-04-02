# Bullhorn

Lightweight FastAPI service that reads posts from a JSON file queue and publishes them to LinkedIn and X (Twitter) on a schedule.

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Install dependencies

```bash
uv sync
```

### Configure environment

```bash
cp .env.example .env
```

Fill in your API credentials in `.env`:

**LinkedIn** — Create an app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/), request the `w_member_social` scope, and generate an OAuth 2.0 access token.

**X / Twitter** — Create a project at [X Developer Portal](https://developer.twitter.com/), enable OAuth 1.0a with read+write permissions, and copy your API key/secret and access token/secret. Free tier allows 1,500 tweets/month.

### Run

```bash
uv run uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Docker

```bash
docker build -t bullhorn .
docker run -p 8000:8000 --env-file .env bullhorn
```

## Adding Posts

POST to `/posts`:

```json
{
  "id": "2026-04-15-my-post",
  "content": "Your post content here.",
  "hashtags": ["Tech", "AI"],
  "platforms": ["linkedin", "x"],
  "scheduled_date": "2026-04-15T09:00:00"
}
```

The scheduler checks every hour (configurable via `SCHEDULER_CRON`) and publishes any pending posts whose `scheduled_date` has passed. You can also trigger immediate publishing via `POST /posts/{id}/publish`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /posts | List all posts (filter with `?status=pending`) |
| GET | /posts/{id} | Get a single post |
| POST | /posts | Add a new post |
| PUT | /posts/{id} | Update a post |
| DELETE | /posts/{id} | Remove a post |
| POST | /posts/{id}/publish | Publish immediately |
| POST | /posts/{id}/skip | Mark as skipped |
| GET | /health | Service health check |
