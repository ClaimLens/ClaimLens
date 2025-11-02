import os
from werkzeug.utils import secure_filename
from PIL import Image
import io
from datetime import datetime

class DocumentProcessor:
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    UPLOAD_FOLDER = 'uploads'
    
    def __init__(self):
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
    
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def save_document(self, file, claim_id):
        """
        Save uploaded document
        Returns: (success, file_path or error_message)
        """
        try:
            # Validate file
            if not file:
                return False, "No file provided"
            
            if not self.is_allowed_file(file.filename):
                return False, f"File type not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > self.MAX_FILE_SIZE:
                return False, "File too large (max 10MB)"
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            original_filename = secure_filename(file.filename)
            filename = f"{claim_id}_{timestamp}_{original_filename}"
            
            # Save file
            file_path = os.path.join(self.UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # Optimize image if it's an image
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                self._optimize_image(file_path)
            
            return True, file_path
            
        except Exception as e:
            return False, f"Upload failed: {str(e)}"
    
    def _optimize_image(self, file_path):
        """Compress and optimize image"""
        try:
            img = Image.open(file_path)
            
            # Resize if too large
            max_dimension = 2048
            if max(img.size) > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save optimized
            img.save(file_path, optimize=True, quality=85)
            
        except Exception as e:
            print(f"Image optimization failed: {e}")
            # Continue anyway, file is already saved
    
    def delete_document(self, file_path):
        """Delete document file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except:
            pass
        return False
    
    def get_document_info(self, file_path):
        """Get document metadata"""
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        return {
            'filename': file_name,
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'path': file_path
        }

# Singleton instance
document_processor = DocumentProcessor()