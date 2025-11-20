import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Inquiry, Application
from database import create_document, get_documents, db

app = FastAPI(title="Illuminati Pvt Ltd API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Illuminati Pvt Ltd backend is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ----- Inquiry Endpoints -----
class InquiryCreateResponse(BaseModel):
    id: str
    message: str


@app.post("/api/inquiries", response_model=InquiryCreateResponse)
def create_inquiry(inquiry: Inquiry):
    try:
        new_id = create_document("inquiry", inquiry)
        return {"id": new_id, "message": "Inquiry received. Our team will contact you shortly."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InquiryOut(Inquiry):
    id: Optional[str] = None


@app.get("/api/inquiries", response_model=List[InquiryOut])
def list_inquiries(limit: int = Query(20, ge=1, le=100)):
    try:
        docs = get_documents("inquiry", {}, limit)
        # Convert ObjectId to string and map fields
        out: List[InquiryOut] = []
        for d in docs:
            d_copy = {k: v for k, v in d.items() if k not in ["_id"]}
            d_copy["id"] = str(d.get("_id")) if d.get("_id") else None
            out.append(InquiryOut(**d_copy))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----- Careers Application Endpoints -----
class ApplicationCreateResponse(BaseModel):
    id: str
    message: str


@app.post("/api/applications", response_model=ApplicationCreateResponse)
def create_application(application: Application):
    try:
        new_id = create_document("application", application)
        return {"id": new_id, "message": "Application submitted. Our HR team will reach out if there's a fit."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ApplicationOut(Application):
    id: Optional[str] = None


@app.get("/api/applications", response_model=List[ApplicationOut])
def list_applications(limit: int = Query(20, ge=1, le=100)):
    try:
        docs = get_documents("application", {}, limit)
        out: List[ApplicationOut] = []
        for d in docs:
            d_copy = {k: v for k, v in d.items() if k not in ["_id"]}
            d_copy["id"] = str(d.get("_id")) if d.get("_id") else None
            out.append(ApplicationOut(**d_copy))
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: expose schemas for tooling
@app.get("/schema")
def get_schema():
    from schemas import User, Product, Inquiry as InquirySchema, Application as ApplicationSchema
    return {
        "user": User.model_json_schema(),
        "product": Product.model_json_schema(),
        "inquiry": InquirySchema.model_json_schema(),
        "application": ApplicationSchema.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
