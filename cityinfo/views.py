import requests
from azure.storage.blob import BlobServiceClient
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings

def get_city_photo(city_name):
    unsplash_url = "https://api.unsplash.com/search/photos"
    params = {
        "query": city_name,
        "client_id": settings.UNSPLASH_ACCESS_KEY,  # Ajoutez votre clé API dans settings
        "per_page": 1,
    }
    response = requests.get(unsplash_url, params=params)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            return results[0]['urls']['regular']  # Retourne l'URL de la photo
    return None




def get_city_details(request):
    if request.method == 'POST':
        city_name = request.POST.get('city', None)
        if not city_name:
            return JsonResponse({'error': 'Veuillez fournir une ville'}, status=400)

        # Récupérer les coordonnées via Azure Maps
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

        result = data['results'][0]
        coordinates = result['position']
        details = {
            'city': city_name,
            'latitude': coordinates['lat'],
            'longitude': coordinates['lon'],
            'address': result.get('address', {}),
        }

        # Ajouter une photo de la ville
        details['photo_url'] = get_city_photo(city_name)

        # Ajouter des endroits touristiques
        #details['tourist_places'] = get_tourist_places(city_name)

        # Sauvegarder dans Azure Blob Storage
        blob_service_client = BlobServiceClient(
            account_url=f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net/",
            credential=settings.AZURE_STORAGE_ACCOUNT_KEY,
        )
        blob_client = blob_service_client.get_blob_client(
            container=settings.AZURE_STORAGE_CONTAINER_NAME,
            blob=f"{city_name}.json",
        )
        blob_client.upload_blob(str(details), overwrite=True)

        # Retourner les résultats dans un template HTML
        return render(request, 'cityinfo/city_details.html', {'details': details})

    return render(request, 'cityinfo/city_form.html')
