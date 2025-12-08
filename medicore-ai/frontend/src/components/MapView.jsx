import React, { useEffect, useRef } from 'react';
import './MapView.css';

const MapView = ({
  lat = 12.9716,
  lng = 77.5946,
  zoom = 13,
  label = 'Nearby Medical Locations',
  places = [],
}) => {
  const mapRef = useRef(null);

  useEffect(() => {
    if (!window.google || !window.google.maps || !mapRef.current) return;

    const center = { lat, lng };
    const map = new window.google.maps.Map(mapRef.current, {
      center,
      zoom,
      mapTypeId: 'roadmap',
    });

    new window.google.maps.Marker({
      position: center,
      map,
      title: 'Approximate location',
      icon: {
        path: window.google.maps.SymbolPath.CIRCLE,
        scale: 6,
        fillColor: '#10b981',
        fillOpacity: 1,
        strokeColor: '#ffffff',
        strokeWeight: 2,
      },
    });

    if (places && places.length > 0) {
      places.forEach((place) => {
        const position = {
          lat: place.location?.lat ?? place.lat,
          lng: place.location?.lng ?? place.lng,
        };

        const marker = new window.google.maps.Marker({
          position,
          map,
          title: place.name || 'Hospital',
        });

        const info = new window.google.maps.InfoWindow({
          content: `
            <div style="max-width:220px">
              <strong>${place.name || 'Hospital/Clinic'}</strong><br/>
              ${place.address || ''}<br/>
              ${place.phone ? 'â˜Ž ' + place.phone + '<br/>' : ''}
              ${place.rating ? 'â­ ' + place.rating : ''}
            </div>
          `,
        });

        marker.addListener('click', () => info.open(map, marker));
      });
    }
  }, [lat, lng, zoom, places]);

  return (
    <div className="map-wrapper">
      <div className="map-header">
        <div className="map-title-row">
          <span className="map-pin">ðŸ“</span>
          <span className="map-title">{label}</span>
        </div>
        <div className="map-subtitle">
          {places?.length
            ? `Found ${places.length} hospital(s)/clinic(s) within ~5 km`
            : 'Searching nearby hospitals...'}
        </div>
      </div>
      <div ref={mapRef} className="map-container" />
      <div className="map-link">
        <a
          href={`https://www.google.com/maps/search/hospitals/@${lat},${lng},14z`}
          target="_blank"
          rel="noreferrer"
        >
          View on Google Maps
        </a>
      </div>
    </div>
  );
};

export default MapView;