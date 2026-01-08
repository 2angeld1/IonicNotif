import React, { useState, useEffect, useRef } from 'react';
import { IonSpinner, IonIcon } from '@ionic/react';
import { homeOutline, briefcaseOutline, starOutline, locationOutline } from 'ionicons/icons';
import { searchLocations } from '../services/geocodingService';
import type { LocationSuggestion, LatLng, FavoritePlace } from '../types';

interface LocationSearchProps {
  label: string;
  placeholder: string;
  value: string;
  onLocationSelect: (location: LatLng, displayName: string) => void;
  color?: string;
  favorites?: FavoritePlace[];
}

const LocationSearch: React.FC<LocationSearchProps> = ({
  placeholder,
  value,
  onLocationSelect,
  color = 'blue',
  favorites = [],
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const debounceRef = useRef<number | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  const handleInputChange = (val: string) => {
    setQuery(val);
    
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (val.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setIsLoading(true);
    debounceRef.current = window.setTimeout(async () => {
      const results = await searchLocations(val);
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
      setIsLoading(false);
    }, 400);
  };

  const handleSelect = (suggestion: LocationSuggestion) => {
    // Acortar el nombre para mostrar
    const shortName = suggestion.display_name.split(',').slice(0, 3).join(', ');
    setQuery(shortName);
    setShowSuggestions(false);
    setSuggestions([]);
    onLocationSelect(
      { lat: parseFloat(suggestion.lat), lng: parseFloat(suggestion.lon) },
      shortName
    );
  };

  const handleFavoriteSelect = (fav: FavoritePlace) => {
    setQuery(fav.name);
    onLocationSelect(fav.location, fav.name);
  };

  const borderColors = {
    blue: 'focus:border-blue-500 focus:ring-blue-500/20',
    green: 'focus:border-emerald-500 focus:ring-emerald-500/20',
    red: 'focus:border-rose-500 focus:ring-rose-500/20',
  };

  return (
    <div className="relative w-full">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          placeholder={placeholder}
          onChange={(e) => handleInputChange(e.target.value)}
          onFocus={() => {
            setIsFocused(true);
            if (suggestions.length > 0) setShowSuggestions(true);
          }}
          onBlur={() => {
            setTimeout(() => {
              setIsFocused(false);
              setShowSuggestions(false);
            }, 200);
          }}
          className={`w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-xs text-gray-800 placeholder-gray-400 transition-all duration-200 focus:outline-none focus:ring-4 focus:bg-white ${borderColors[color as keyof typeof borderColors]}`}
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <IonSpinner name="crescent" className="w-3 h-3 text-gray-400" />
          </div>
        )}
      </div>

      {/* Dropdown de Favoritos (Solo visible al hacer foco y sin texto) */}
      {isFocused && favorites.length > 0 && !query && (
        <div className="absolute z-[1002] w-full bg-white mt-1 rounded-xl shadow-xl border border-gray-100 p-2">
          <div className="text-[10px] font-bold text-gray-400 mb-1 px-1">TUS LUGARES</div>
          <div className="flex flex-col gap-1 max-h-48 overflow-y-auto">
            {favorites.map((fav) => (
              <button
                key={fav.id}
                onClick={() => handleFavoriteSelect(fav)}
                className="flex items-center gap-2 px-2 py-2 hover:bg-gray-50 rounded-lg transition-colors w-full text-left group"
              >
                <div className={`p-1.5 rounded-lg transition-colors ${fav.type === 'home' ? 'bg-blue-100 group-hover:bg-blue-200' :
                    fav.type === 'work' ? 'bg-amber-100 group-hover:bg-amber-200' :
                      'bg-pink-100 group-hover:bg-pink-200'
                  }`}>
                  <IonIcon
                    icon={
                      fav.type === 'home' ? homeOutline :
                        fav.type === 'work' ? briefcaseOutline :
                          fav.type === 'favorite' ? starOutline :
                            locationOutline
                    }
                    className={`w-4 h-4 ${fav.type === 'home' ? 'text-blue-600' :
                        fav.type === 'work' ? 'text-amber-600' :
                          'text-pink-600'
                      }`}
                  />
                </div>
                <span className="text-xs font-bold text-gray-700">{fav.name}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-[1001] w-full bg-white mt-1 rounded-xl shadow-xl border border-gray-100 max-h-48 overflow-y-auto">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.place_id}
              onClick={() => handleSelect(suggestion)}
              className="w-full text-left px-4 py-2 hover:bg-blue-50 transition-colors duration-150 border-b border-gray-50 last:border-b-0"
            >
              <p className="text-xs text-gray-800 truncate">
                {suggestion.display_name.split(',').slice(0, 2).join(', ')}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LocationSearch;
