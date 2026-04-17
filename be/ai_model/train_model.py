import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import DataLoader, Dataset
import torch.optim as optim
from PIL import Image
import cv2
import os

class FaceCropDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        self.transform = transform
        self.samples = []
        self.class_to_idx = {}
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        classes = sorted(entry.name for entry in os.scandir(root_dir) if entry.is_dir())
        self.classes = classes
        self.class_to_idx = {cls_name: idx for idx, cls_name in enumerate(classes)}

        for cls in classes:
            cls_path = os.path.join(root_dir, cls)
            for file in os.listdir(cls_path):
                if file.lower().endswith((".jpg", ".jpeg", ".png")):
                    self.samples.append((os.path.join(cls_path, file), self.class_to_idx[cls]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            raise ValueError(f"Cannot read image: {img_path}")

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        if len(faces) == 0:
            face_crop = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        else:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_crop = img_bgr[y:y+h, x:x+w]
            face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)

        img_pil = Image.fromarray(face_crop)
        if self.transform:
            img_pil = self.transform(img_pil)

        return img_pil, label


async def train_face_model():
    """Train face recognition model"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Using device: {device}")

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225]),
    ])

    # Load dataset
    train_dataset = FaceCropDataset("dataset", transform=transform)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    classes = train_dataset.classes
    num_classes = len(classes)

    print(f"✅ Dataset loaded: {num_classes} classes, {len(train_dataset)} images")

    # Load ResNet18 pretrained
    model = models.resnet18(pretrained=True)
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=0.001)

    # Training
    EPOCHS = 5
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0
        correct = 0
        total = 0
        for imgs, labels in train_loader:
            imgs, labels = imgs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            _, preds = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (preds == labels).sum().item()
        
        print(f"Epoch [{epoch+1}/{EPOCHS}] - Loss: {running_loss/len(train_loader):.4f} - Acc: {100*correct/total:.2f}%")

    torch.save(model.state_dict(), "resnet18_face.pth")
    print("✅ Model saved as resnet18_face.pth")
