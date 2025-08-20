from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

@csrf_exempt
def ajax_file_upload(request):
    if request.method == "POST" and request.FILES.get("file"):
        upload_file = request.FILES["file"]

        # Klasör seçimi
        if "image" in upload_file.content_type:
            folder = "uploads/images"
        elif "video" in upload_file.content_type:
            folder = "uploads/videos"
        else:
            folder = "uploads/general"

        # Kaydetme yolu (relative path olacak)
        save_path = os.path.join(folder, upload_file.name)

        # Django storage ile kaydet (aynı isimde varsa otomatik değiştirilir)
        file_name = default_storage.save(save_path, ContentFile(upload_file.read()))

        # Tarayıcıya verilecek URL
        file_url = default_storage.url(file_name)

        return JsonResponse({
            "success": True,
            "url": file_url,   # Önizleme için (template'te gösterilecek)
            "path": file_name  # Model field'a kaydedilecek değer (image.name veya video.name)
        })

    return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)
