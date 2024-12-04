import requests
from azure.storage.blob import BlobServiceClient
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

def get_city_details(request):
    if request.method == 'POST':
        city_name = request.POST.get('city', None)
        if not city_name:
            return JsonResponse({'error': 'Veuillez fournir une ville'}, status=400)

        # Étape 1 : Récupérer les coordonnées via Azure Maps
        maps_url = f"https://atlas.microsoft.com/search/address/json"
        params = {
            "subscription-key": settings.AZURE_MAPS_SUBSCRIPTION_KEY,
            "api-version": "1.0",
            "query": city_name,
        }
        response = requests.get(maps_url, params=params)
        if response.status_code != 200:
            return JsonResponse({'error': 'Erreur avec Azure Maps'}, status=500)

        data = response.json()
        if not data.get('results'):
            return JsonResponse({'error': 'Ville introuvable'}, status=404)

        # Extraire les informations pertinentes
        result = data['results'][0]
        coordinates = result['position']
        details = {
            'city': city_name,
            'latitude': coordinates['lat'],
            'longitude': coordinates['lon'],
            'address': result.get('address', {}),
        }

        # Étape 2 : Sauvegarder dans Azure Blob Storage
        blob_service_client = BlobServiceClient(
            account_url=f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/",
            credential=settings.AZURE_STORAGE_ACCOUNT_KEY,
        )
        blob_client = blob_service_client.get_blob_client(
            container=settings.AZURE_STORAGE_CONTAINER_NAME,
            blob=f"{city_name}.json",
        )
        blob_client.upload_blob(str(details), overwrite=True)

        return JsonResponse({'message': 'Données récupérées et sauvegardées', 'details': details})

    return render(request, 'cityinfo/city_form.html')
