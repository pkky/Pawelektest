document.addEventListener('DOMContentLoaded', function() {
    var map = L.map('map').setView(cityCoords['warszawa'], 13);
    var shopLayer = L.layerGroup().addTo(map);
    var shopData = {}; // To store shop data

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { 
        maxZoom: 19, 
        attribution: '© OpenStreetMap contributors' 
    }).addTo(map);

    function loadShopsForCity(city) {
        fetch(`static/localizations/${city}.geojson`)
            .then(response => response.json())
            .then(data => {
                shopData[city] = data; // Store shop data for each city
            });
    }

    function showNearbyShops(lat, lng) {
        shopLayer.clearLayers(); // Clear existing shop markers
        shopData[citySelect.value].features.forEach(feature => {
            feature.geometry.coordinates.forEach(coord => {
                var distance = getDistance(lat, lng, coord[0], coord[1]);
                if (distance <= 1000) { // Check if within 1000 meters
                    var shopIcon = L.icon({
                        iconUrl: feature.properties.image,
                        iconSize: [50, 50],
                        iconAnchor: [25, 50],
                        popupAnchor: [0, -50]
                    });
                    L.marker([coord[0], coord[1]], {icon: shopIcon})
                        .bindPopup(feature.properties.shopName)
                        .addTo(shopLayer);
                }
            });
        });
    }

    function getDistance(lat1, lng1, lat2, lng2) {
        // Calculate distance between two points in meters
        return map.distance([lat1, lng1], [lat2, lng2]);
    }

    function updateMap(city) {
        map.setView(cityCoords[city], 13);
        map.eachLayer(function(layer) {
            if (layer instanceof L.Marker) {
                map.removeLayer(layer);
            }
        });

        roomData.forEach(function(room) {
            if (room.latitude && room.longitude) {
                var roomMarker = L.marker([room.latitude, room.longitude]).addTo(map);
                var popupContent = "<b>" + room.name + "</b><br>" +
                                   "Price: " + room.price + "<br>" +
                                   "Surface: " + room.surface + "<br>" +
                                   "<a href='" + room.link + "' target='_blank'>View Details</a>";
                roomMarker.bindPopup(popupContent);

                roomMarker.on('click', function() {
                    showNearbyShops(room.latitude, room.longitude);
                });
            }
        });
    }

    // Clear shop markers when map is clicked (deselecting a room)
    map.on('click', function() {
        shopLayer.clearLayers();
    });

    var citySelect = document.getElementById('city');
    citySelect.addEventListener('change', function() {
        updateMap(this.value);
        loadShopsForCity(this.value); // Load shops for the selected city
    });

    loadShopsForCity(citySelect.value); // Initial load for default city
    updateMap(citySelect.value); // Update on load
});
