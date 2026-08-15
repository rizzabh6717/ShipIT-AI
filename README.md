# ShipIT AI — AI-Powered Route Matching Logistics Platform

![ShipIT AI Banner](https://github.com/user-attachments/assets/b3dcb942-7f44-4e4b-86ae-70439577d504)

**ShipIT AI** is an AI-powered crowdsourced logistics platform that matches senders with drivers who are already traveling along compatible routes. Instead of relying solely on dedicated delivery fleets, drivers publish their routes and available capacity, while senders create parcel requests. The platform uses **semantic route retrieval with pgvector** and **LangChain-powered LLM ranking** to recommend the most suitable drivers for each delivery.

The goal is to reduce delivery costs, minimize empty vehicle miles, and provide explainable AI-driven matching decisions.

---

## Features

- **Driver Route Publishing** — Drivers can publish travel routes, vehicle type, capacity, and availability.
- **Parcel Creation** — Senders create parcel requests with pickup/drop locations, weight, dimensions, budget, and delivery deadline.
- **AI Driver Matching** — Uses **pgvector semantic similarity search** to retrieve compatible driver routes.
- **LLM-Based Ranking** — A **LangChain-powered LLM re-ranking layer** evaluates route overlap, detour distance, deadline feasibility, reliability, and capacity to produce intelligent driver recommendations.
- **Explainable Recommendations** — Every AI recommendation includes a human-readable explanation of why the driver was ranked highly.
- **Driver Approval Workflow** — The sender selects a preferred driver, who can then accept or reject the delivery request.
- **Live Delivery Tracking** — Track parcel status from request creation to final delivery.
- **Proof of Delivery** — Drivers upload a delivery photo upon completion, which the sender can view from the dashboard.
- **Feedback & Reliability Scoring** — Sender ratings update driver reliability, which influences future AI ranking.

---

## Technology Stack

### Frontend

- **React**
- **TanStack Router**
- **React Query**
- **TypeScript**
- **Tailwind CSS v4**
- **Framer Motion**
- **Lucide React**

### Backend

- **FastAPI**
- **Async SQLAlchemy**
- **Alembic**
- **JWT Authentication**
- **PostgreSQL 18**
- **pgvector**

### AI Layer

- **LangChain**
- **OpenRouter / OpenAI Compatible LLMs**
- **Semantic Route Retrieval**
- **LLM Re-ranking**
- **Explainable AI Recommendations**

---

## Architecture

```text
Driver Routes
      │
      ▼
PostgreSQL + pgvector
      │
Semantic Retrieval
      │
      ▼
Candidate Driver Routes
      │
      ▼
LangChain LLM Re-ranking
      │
      ▼
Explainable Driver Recommendations
      │
      ▼
Driver Approval
      │
      ▼
Pickup → In Transit → Delivered
```

The system follows a modern **React + FastAPI** architecture with an AI-powered matching pipeline.

- **Frontend** provides sender and driver dashboards, parcel creation, route publishing, AI matching, and tracking.
- **FastAPI Backend** exposes REST APIs and handles authentication, routing, parcel management, delivery requests, and proof-of-delivery uploads.
- **PostgreSQL + pgvector** stores route embeddings and performs semantic similarity retrieval.
- **LangChain** performs LLM-based reasoning and re-ranking of retrieved driver candidates.

---

## AI Matching Pipeline

1. **Driver publishes a route**
2. **Sender creates a parcel**
3. **Semantic retrieval** finds compatible driver routes using **pgvector**
4. **LLM re-ranking** evaluates trade-offs across:
   - Route overlap
   - Pickup detour
   - Delivery deadline
   - Driver reliability
   - Vehicle capacity
5. **Ranked driver recommendations** are returned with explanations
6. **Sender selects a driver**
7. **Driver accepts or rejects**
8. **Delivery is completed with proof of delivery**

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a user |
| POST | `/api/auth/login` | Login and obtain JWT token |
| POST | `/api/routes` | Publish a driver route |
| GET | `/api/routes` | List active routes |
| POST | `/api/parcels` | Create a parcel |
| GET | `/api/parcels` | List sender parcels |
| POST | `/api/ai/match` | AI route matching and ranking |
| POST | `/api/deliveries/requests` | Send a delivery request |
| POST | `/api/deliveries/requests/{id}/accept` | Driver accepts request |
| POST | `/api/deliveries/requests/{id}/reject` | Driver rejects request |
| POST | `/api/deliveries/requests/{id}/pickup` | Mark parcel as picked up |
| POST | `/api/deliveries/requests/{id}/upload` | Upload proof of delivery photo |
| POST | `/api/deliveries/requests/{id}/rate` | Submit driver feedback and rating |

---

## Getting Started

### Clone the Repository

```bash
git clone <repository-url>
cd shipit-ai
```

### Backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

**Windows**

```bash
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/shipit
JWT_SECRET_KEY=your_secret_key
OPENROUTER_API_KEY=your_api_key
```

Run database migrations:

```bash
alembic upgrade head
```

Start the backend server:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend: **http://localhost:8080**  
Backend: **http://localhost:8000**

---

## Project Workflow

```text
Driver publishes route
        │
        ▼
Sender creates parcel
        │
        ▼
AI retrieves compatible routes
        │
        ▼
LLM ranks the best drivers
        │
        ▼
Sender selects a driver
        │
        ▼
Driver accepts request
        │
        ▼
Pickup → In Transit → Delivered
        │
        ▼
Proof of Delivery + Feedback
```

---

## Future Improvements

- Real-time WebSocket notifications
- Geospatial route overlap using PostGIS
- LLM evaluation harness for ranking quality
- Multi-driver route optimization
- Dynamic pricing based on demand and traffic
- Docker-based deployment
- Kubernetes scaling support

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Open a Pull Request

---


**ShipIT AI** demonstrates semantic retrieval, LLM reasoning, explainable AI recommendations, FastAPI backend engineering, and production-style logistics workflow design in a single end-to-end project.
