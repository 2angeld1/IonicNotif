import type { LocationSuggestion, RouteInfo } from '../types';

/**
 * Buscar ubicaciones por texto usando Google Maps Places Autocomplete
 * Usamos el servicio de Google Maps que se carga globalmente
 */
export const searchLocations = async (query: string): Promise<LocationSuggestion[]> => {
  if (!query || query.length < 3) return [];

  return new Promise((resolve) => {
    if (!window.google || !window.google.maps || !window.google.maps.places) {
      console.error('Google Maps Places library not loaded');
      resolve([]);
      return;
    }

    const service = new google.maps.places.AutocompleteService();
    service.getPlacePredictions(
      {
        input: query,
        locationBias: {
          radius: 50000,
          center: { lat: 8.9824, lng: -79.5199 } // Ciudad de Panamá como bias
        },
        // sessionToken: sessionToken, // Opcional, ayuda con costos pero puede limitar si no se maneja bien
        // componentRestrictions: { country: 'pa' }, // Comentamos para ampliar la búsqueda si no encuentra nada
      },
      async (predictions, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK || !predictions) {
          resolve([]);
          return;
        }

        // Google Places Autocomplete no da lat/lng directamente, necesitamos geocodificar o usar PlacesService
        // Para no hacer 10 peticiones de geocodificación, devolveremos los resultados y el componente se encargará de obtener la posición al seleccionar
        const results: LocationSuggestion[] = predictions.map((p) => ({
          display_name: p.description,
          lat: '0', // Se obtendrá al seleccionar
          lon: '0',
          place_id: p.place_id as any, // Usamos place_id de Google
        }));

        resolve(results);
      }
    );
  });
};

/**
 * Obtener detalles de una ubicación (específicamente lat/lng) usando place_id
 */
export const getPlaceDetails = async (placeId: string): Promise<{ lat: number; lng: number } | null> => {
  return new Promise((resolve) => {
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ placeId: placeId }, (results, status) => {
      if (status === google.maps.GeocoderStatus.OK && results && results[0]) {
        const loc = results[0].geometry.location;
        resolve({ lat: loc.lat(), lng: loc.lng() });
      } else {
        console.error('Error en geocodificación:', status);
        resolve(null);
      }
    });
  });
};

/**
 * Obtener la ruta entre dos puntos usando Google Maps Directions Service
 */
export const getRoute = async (
  start: { lat: number; lng: number },
  end: { lat: number; lng: number },
  provideAlternatives: boolean = false
): Promise<RouteInfo | null> => {
  return new Promise((resolve) => {
    const directionsService = new google.maps.DirectionsService();

    directionsService.route(
      {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING,
        provideRouteAlternatives: provideAlternatives,
        drivingOptions: {
          departureTime: new Date(),
          trafficModel: google.maps.TrafficModel.BEST_GUESS
        }
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result && result.routes[0]) {
          const route = result.routes[0];
          const leg = route.legs[0];

          const path = route.overview_path.map(p => [p.lng(), p.lat()] as [number, number]);

          const steps = leg.steps.map(step => {
            // Analizar tráfico (Google a veces no da duration_in_traffic por step en API Standard, 
            // pero si lo da, lo usamos. Si no, asumimos normal por defecto)
            // @ts-ignore - duration_in_traffic a veces existe aunque los tipos no lo digan
            const trafficDur = step.duration_in_traffic?.value;
            const normalDur = step.duration?.value || 0;

            let status: 'normal' | 'moderate' | 'heavy' | 'severe' = 'normal';
            if (trafficDur) {
              const ratio = trafficDur / normalDur;
              if (ratio > 2.0) status = 'severe';
              else if (ratio > 1.5) status = 'heavy';
              else if (ratio > 1.2) status = 'moderate';
            }

            // Convertir Geometry a LatLng[]
            // @ts-ignore - lat_lngs o path suele venir en el objeto step nativo
            const stepPath = (step.lat_lngs || step.path || []).map((p: any) => ({
              lat: typeof p.lat === 'function' ? p.lat() : p.lat,
              lng: typeof p.lng === 'function' ? p.lng() : p.lng
            }));

            return {
              instruction: step.instructions.replace(/<[^>]*>?/gm, ''),
              distance: step.distance?.value || 0,
              duration: step.duration?.value || 0,
              name: '',
              location: step.end_location ? {
                lat: step.end_location.lat(),
                lng: step.end_location.lng()
              } : undefined,
              path: stepPath,
              traffic_status: status
            };
          });

          resolve({
            distance: leg.distance?.value || 0,
            duration: leg.duration?.value || 0,
            duration_in_traffic: leg.duration_in_traffic?.value || leg.duration?.value || 0,
            coordinates: path,
            steps: steps
          }); 

        } else {
          console.error('Error obteniendo ruta:', status);
          resolve(null);
        }
      }
    );
  });
};

/**
 * Obtener múltiples rutas alternativas de Google Maps
 */
export const getRouteAlternatives = async (
  start: { lat: number; lng: number },
  end: { lat: number; lng: number }
): Promise<RouteInfo[]> => {
  return new Promise((resolve) => {
    const directionsService = new google.maps.DirectionsService();

    directionsService.route(
      {
        origin: start,
        destination: end,
        travelMode: google.maps.TravelMode.DRIVING,
        provideRouteAlternatives: true,
        drivingOptions: {
          departureTime: new Date(),
          trafficModel: google.maps.TrafficModel.BEST_GUESS
        }
      },
      (result, status) => {
        if (status === google.maps.DirectionsStatus.OK && result && result.routes.length > 0) {
          const alternatives: RouteInfo[] = result.routes.map((route, index) => {
            const leg = route.legs[0];
            const path = route.overview_path.map(p => [p.lng(), p.lat()] as [number, number]);

            const steps = leg.steps.map(step => {
              // @ts-ignore
              const trafficDur = step.duration_in_traffic?.value;
              const normalDur = step.duration?.value || 0;

              let trafficStatus: 'normal' | 'moderate' | 'heavy' | 'severe' = 'normal';
              if (trafficDur) {
                const ratio = trafficDur / normalDur;
                if (ratio > 2.0) trafficStatus = 'severe';
                else if (ratio > 1.5) trafficStatus = 'heavy';
                else if (ratio > 1.2) trafficStatus = 'moderate';
              }

              // @ts-ignore
              const stepPath = (step.lat_lngs || step.path || []).map((p: any) => ({
                lat: typeof p.lat === 'function' ? p.lat() : p.lat,
                lng: typeof p.lng === 'function' ? p.lng() : p.lng
              }));

              return {
                instruction: step.instructions.replace(/<[^>]*>?/gm, ''),
                distance: step.distance?.value || 0,
                duration: step.duration?.value || 0,
                name: '',
                location: step.end_location ? {
                  lat: step.end_location.lat(),
                  lng: step.end_location.lng()
                } : undefined,
                path: stepPath,
                traffic_status: trafficStatus
              };
            });

            return {
              distance: leg.distance?.value || 0,
              duration: leg.duration?.value || 0,
              duration_in_traffic: leg.duration_in_traffic?.value || leg.duration?.value || 0,
              coordinates: path,
              steps: steps,
              routeIndex: index,
              summary: route.summary || `Ruta ${index + 1}`
            };
          });

          resolve(alternatives);
        } else {
          console.error('Error obteniendo rutas alternativas:', status);
          resolve([]);
        }
      }
    );
  });
};

/**
 * Geocodificación inversa - obtener dirección desde coordenadas
 */
export const reverseGeocode = async (lat: number, lng: number): Promise<string> => {
  return new Promise((resolve) => {
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ location: { lat, lng } }, (results, status) => {
      if (status === google.maps.GeocoderStatus.OK && results && results[0]) {
        resolve(results[0].formatted_address);
      } else {
        console.error('Error en geocodificación inversa:', status);
        resolve('Ubicación desconocida');
      }
    });
  });
};
