import { useState, useRef, useEffect } from 'react';

export default function FaceCaptureModal({ isOpen, onClose, onCapture }) {
  const [countdown, setCountdown] = useState(5);
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedCount, setCapturedCount] = useState(0);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const captureIntervalRef = useRef(null);
  const capturedImages = useRef([]);

  useEffect(() => {
    if (isOpen) {
      startCamera();
    } else {
      cleanup();
    }

    return () => cleanup();
  }, [isOpen]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user' } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error('Camera error:', err);
      alert('Không thể truy cập camera');
      onClose();
    }
  };

  const startCapture = () => {
    setIsCapturing(true);
    capturedImages.current = [];
    setCapturedCount(0);
    
    // Countdown
    let count = 5;
    setCountdown(count);
    const countdownTimer = setInterval(() => {
      count--;
      setCountdown(count);
      if (count <= 0) {
        clearInterval(countdownTimer);
      }
    }, 1000);

    // Start capturing after countdown
    setTimeout(() => {
      startCapturing();
    }, 5000);
  };

  const startCapturing = () => {
    let captureCount = 0;
    const maxCaptures = 20;
    const captureDuration = 5000; // 5 giây
    const captureInterval = captureDuration / maxCaptures; // 5000ms / 20 = 250ms
    
    captureIntervalRef.current = setInterval(() => {
      if (captureCount >= maxCaptures) {
        clearInterval(captureIntervalRef.current);
        finishCapture();
        return;
      }
      
      captureFrame();
      captureCount++;
      setCapturedCount(captureCount);
    }, captureInterval); // 250ms giữa mỗi ảnh = 20 ảnh trong 5 giây
  };

  const captureFrame = () => {
    if (!videoRef.current) return;
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0);
    
    canvas.toBlob((blob) => {
      if (blob) {
        capturedImages.current.push(blob);
      }
    }, 'image/jpeg', 0.8);
  };

  const finishCapture = () => {
    onCapture(capturedImages.current);
    cleanup();
    onClose();
  };

  const cleanup = () => {
    if (captureIntervalRef.current) {
      clearInterval(captureIntervalRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    capturedImages.current = [];
    setIsCapturing(false);
    setCountdown(5);
    setCapturedCount(0);
  };

  const handleCancel = () => {
    cleanup();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black/30 flex items-center justify-center z-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl p-8 max-w-2xl w-full mx-4 shadow-2xl">
        {/* Header with close button */}
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-2xl font-bold text-gray-800">Chụp khuôn mặt</h3>
          <button
            onClick={handleCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="relative bg-gray-900 rounded-xl overflow-hidden mb-6">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-96 object-cover"
          />
          
          {/* Countdown overlay */}
          {isCapturing && countdown > 0 && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-white text-9xl font-bold drop-shadow-2xl animate-pulse">
                {countdown}
              </div>
            </div>
          )}

          {/* Capture progress */}
          {isCapturing && countdown === 0 && (
            <div className="absolute top-4 left-4 bg-green-500 text-white px-4 py-2 rounded-lg font-bold">
              Đã chụp: {capturedCount}/20
            </div>
          )}
        </div>

        <div className="text-center mb-4">
          {!isCapturing ? (
            <div className="text-gray-600">
              <p className="font-semibold mb-2">📸 Hướng dẫn:</p>
              <p>Nhấn "Bắt đầu chụp" và nhìn thẳng vào camera.</p>
              <p className="text-sm mt-1">Hệ thống sẽ đếm ngược 5 giây, sau đó tự động chụp 20 ảnh trong 5 giây.</p>
            </div>
          ) : countdown > 0 ? (
            <div className="text-blue-600 font-semibold">
              Chuẩn bị... Hãy nhìn thẳng vào camera
            </div>
          ) : (
            <div className="text-green-600 font-semibold">
              Đang chụp {capturedCount}/20... Hãy di chuyển khuôn mặt nhẹ nhàng
            </div>
          )}
        </div>

        {!isCapturing && (
          <div className="flex gap-3">
            <button
              onClick={startCapture}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold transition-colors"
            >
              Bắt đầu chụp
            </button>
            <button
              onClick={handleCancel}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-semibold transition-colors"
            >
              Hủy
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
