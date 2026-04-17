from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import List
import numpy as np
import cv2
import os
import shutil

from ai_model.face_recognition import face_recognition_model
from ai_model.train_model import train_face_model
from database import SessionLocal
from models.user import User

router = APIRouter(prefix="/api/face", tags=["Face Recognition"])


@router.post("/upload")
async def upload_face_images(
    images: List[UploadFile] = File(...),
    user_id: int = Form(...),
):
    """Upload face images for a user and train the model"""
    db = SessionLocal()
    try:
        # Get user info
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create directory for user's face images
        save_dir = f"dataset/{user.full_name}"
        os.makedirs(save_dir, exist_ok=True)
        
        saved_files = []
        for img in images:
            filepath = os.path.join(save_dir, img.filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            saved_files.append(img.filename)
        
        print(f"✅ Saved {len(saved_files)} images for {user.full_name}")
        
        # Train model with new data
        print("🔹 Training model with new data...")
        await train_face_model()
        
        # Reload model and features
        print("🔹 Reloading model and features...")
        face_recognition_model.initialize()
        
        return {
            "status": "success",
            "message": f"Added {len(saved_files)} images for {user.full_name} and trained model",
            "files": saved_files
        }
    finally:
        db.close()


@router.post("/recognize")
async def recognize_faces(images: List[UploadFile] = File(...)):
    """Recognize faces from uploaded images using voting mechanism"""
    print(f"🔹 Received {len(images)} images for recognition")
    
    vote_counter = {}
    total = len(images)
    
    for idx, img_file in enumerate(images):
        print(f"Processing image {idx + 1}/{total}: {img_file.filename}")
        
        # Read uploaded image
        img_bytes = await img_file.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        cv_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if cv_img is None:
            print(f"❌ Failed to decode image {idx + 1}")
            continue
        
        # Crop face
        face = face_recognition_model.crop_face_from_array(cv_img)
        
        if face is None:
            print(f"❌ No face detected in image {idx + 1}")
            continue
        
        # Recognize face
        person, dist = face_recognition_model.recognize_face(face)
        print(f"✅ Image {idx + 1}: {person} (distance: {dist:.3f})")
        
        # Count votes
        if person not in vote_counter:
            vote_counter[person] = 0
        vote_counter[person] += 1
        
        # If any person gets 10 votes and is not Unknown, return immediately
        if vote_counter[person] >= 10 and person != "Unknown":
            print(f"🎉 Recognition successful: {person} with {vote_counter[person]} votes")
            return {
                "status": "success",
                "person": person,
                "correct": vote_counter[person],
                "total": total,
                "distance": float(dist)
            }
    
    # If no one reached 10 votes
    print(f"❌ Recognition failed. Votes: {vote_counter}")
    return {
        "status": "fail",
        "person": "Unknown",
        "votes": vote_counter,
        "total": total
    }


@router.get("/users")
async def get_face_users():
    """Get list of users with face data"""
    dataset_dir = "dataset"
    if not os.path.exists(dataset_dir):
        return {"users": []}
    
    users = []
    for person in os.listdir(dataset_dir):
        person_dir = os.path.join(dataset_dir, person)
        if os.path.isdir(person_dir):
            image_count = len([f for f in os.listdir(person_dir) 
                             if f.lower().endswith((".jpg", ".png", ".jpeg"))])
            users.append({
                "name": person,
                "image_count": image_count
            })
    
    return {"users": users}


@router.delete("/users/{user_name}")
async def delete_face_user(user_name: str):
    """Delete face data for a user"""
    dataset_dir = f"dataset/{user_name}"
    
    if not os.path.exists(dataset_dir):
        raise HTTPException(status_code=404, detail="User face data not found")
    
    try:
        shutil.rmtree(dataset_dir)
        print(f"✅ Deleted face data for {user_name}")
        
        # Retrain model
        print("🔹 Retraining model...")
        await train_face_model()
        
        # Reload model and features
        face_recognition_model.initialize()
        
        return {
            "status": "success",
            "message": f"Deleted face data for {user_name} and retrained model"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete-folder/{folder_name}")
async def delete_face_folder(folder_name: str):
    """Delete face data folder without retraining (for replacing face)"""
    dataset_dir = f"dataset/{folder_name}"
    
    if not os.path.exists(dataset_dir):
        return {
            "status": "success",
            "message": "Folder not found or already deleted"
        }
    
    try:
        shutil.rmtree(dataset_dir)
        print(f"✅ Deleted face folder for {folder_name}")
        
        return {
            "status": "success",
            "message": f"Deleted face folder for {folder_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain")
async def retrain_model():
    """Manually trigger model retraining"""
    try:
        print("🔹 Starting manual model retraining...")
        await train_face_model()
        face_recognition_model.initialize()
        
        return {
            "status": "success",
            "message": "Model retrained successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
