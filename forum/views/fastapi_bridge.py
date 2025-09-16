import os
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse

FASTAPI_URL = "http://63.179.88.40/hairfastgan/"

def send_to_fastapi(request):
    print("Incoming request:", request.method)

    if request.method == "POST":
        # Get all 3 uploaded images
        image1 = request.FILES.get("image1")
        image2 = request.FILES.get("image2") 
        image3 = request.FILES.get("image3")

        print("Uploaded files received:")
        print(" - image1:", image1.name if image1 else None)
        print(" - image2:", image2.name if image2 else None)
        print(" - image3:", image3.name if image3 else None)

        # Check if all images are uploaded
        if not all([image1, image2, image3]):
            print("Missing one or more images")
            return JsonResponse({"error": "All 3 images are required"}, status=400)

        try:
            # Prepare files for FastAPI
            files = {
                "file1": (image1.name, image1.read(), image1.content_type),
                "file2": (image2.name, image2.read(), image2.content_type),
                "file3": (image3.name, image3.read(), image3.content_type)
            }
            print("Sending files to FastAPI:", FASTAPI_URL)

            response = requests.post(FASTAPI_URL, files=files)
            print("Response from FastAPI:", response.status_code)

            if response.status_code == 200:
                print("FastAPI returned image successfully")
                return HttpResponse(response.content, content_type="image/png")
            else:
                print("❌ FastAPI error:", response.text)
                return JsonResponse({
                    "error": "FastAPI failed", 
                    "details": response.text,
                    "status": response.status_code
                }, status=500)
                
        except requests.exceptions.RequestException as e:
            print("Request to FastAPI failed:", str(e))
            return JsonResponse({"error": "Request to FastAPI failed", "details": str(e)}, status=500)

    print("⚠️ Invalid request method:", request.method)
    return JsonResponse({"error": "Invalid request method"}, status=405)
