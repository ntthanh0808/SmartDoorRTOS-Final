import torch
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import numpy as np
import cv2
import os

class FaceRecognitionModel:
    def __init__(self):
        self.DATASET_DIR = "dataset"
        self.MODEL_PATH = "resnet18_face.pth"
        self.THRESHOLD = 0.7
        self.DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = None
        self.known_features = None
        self.classes = None
        self.face_cascade = None
        self.transform = None
        
    def initialize(self):
        """Load model and extract features from dataset"""
        print("🔹 Initializing face recognition model...")
        
        # Load face cascade
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        
        # Define transform
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])
        
        # Load classes
        if not os.path.exists(self.DATASET_DIR):
            print("⚠️ Dataset directory not found")
            self.classes = []
            self.known_features = {}
            return
            
        self.classes = [
            c for c in os.listdir(self.DATASET_DIR)
            if os.path.isdir(os.path.join(self.DATASET_DIR, c))
        ]
        
        if len(self.classes) == 0:
            print("⚠️ No classes found in dataset")
            self.known_features = {}
            return
        
        # Load model
        if not os.path.exists(self.MODEL_PATH):
            print("⚠️ Model file not found. Please train the model first.")
            self.known_features = {}
            return
            
        self.model = models.resnet18(pretrained=False)
        num_ftrs = self.model.fc.in_features
        self.model.fc = torch.nn.Linear(num_ftrs, len(self.classes))
        self.model.load_state_dict(torch.load(self.MODEL_PATH, map_location=self.DEVICE))
        self.model.eval().to(self.DEVICE)
        
        # Extract known features
        print("🔹 Extracting features from dataset...")
        self.known_features = {}
        
        for person in self.classes:
            person_dir = os.path.join(self.DATASET_DIR, person)
            feature_list = []
            
            for file in os.listdir(person_dir):
                if file.lower().endswith((".jpg", ".png", ".jpeg")):
                    img_path = os.path.join(person_dir, file)
                    img = self.crop_face(img_path)
                    if img is not None:
                        f = self.extract_feature(img)
                        feature_list.append(f)
            
            if feature_list:
                self.known_features[person] = np.mean(feature_list, axis=0)
        
        print(f"✅ Model initialized with {len(self.classes)} classes")
    
    def extract_feature(self, img):
        """Extract feature vector from face image"""
        if self.model is None:
            raise ValueError("Model not initialized")
            
        img_tensor = self.transform(img).unsqueeze(0).to(self.DEVICE)
        with torch.no_grad():
            x = self.model.conv1(img_tensor)
            x = self.model.bn1(x)
            x = self.model.relu(x)
            x = self.model.maxpool(x)
            x = self.model.layer1(x)
            x = self.model.layer2(x)
            x = self.model.layer3(x)
            x = self.model.layer4(x)
            x = self.model.avgpool(x)
            x = torch.flatten(x, 1)
            x = F.normalize(x, p=2, dim=1)
        return x.cpu().numpy()[0]
    
    def crop_face(self, img_path):
        """Crop face from image file"""
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            return None
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5
        )
        if len(faces) == 0:
            return Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
        face_crop = img_bgr[y:y+h, x:x+w]
        return Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
    
    def crop_face_from_array(self, cv_img):
        """Crop face from OpenCV image array (BGR format)"""
        if cv_img is None:
            return None
        
        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(60, 60)
        )
        
        if len(faces) == 0:
            return None
        
        # Get largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face = cv_img[y:y+h, x:x+w]
        
        # Convert to PIL Image
        return Image.fromarray(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
    
    def recognize_face(self, face_img):
        """Recognize face from PIL Image"""
        if self.model is None or not self.known_features:
            return "Unknown", 999.0
        
        feat = self.extract_feature(face_img)
        min_dist = float("inf")
        identity = "Unknown"
        
        for name, ref_feat in self.known_features.items():
            dist = np.linalg.norm(feat - ref_feat)
            if dist < min_dist:
                min_dist = dist
                identity = name
        
        if min_dist > self.THRESHOLD:
            identity = "Unknown"
        
        return identity, min_dist


# Global instance
face_recognition_model = FaceRecognitionModel()
