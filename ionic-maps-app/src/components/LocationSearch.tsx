import React, { useState, useEffect, useRef } from 'react';
import { IonSpinner } from '@ionic/react';
import { searchLocations } from '../services/geocodingService';
import type { LocationSuggestion, LatLng } from '../types';

interface LocationSearchProps {
  label: string;
  placeholder: string;
  value: string;
  onLocationSelect: (location: LatLng, displayName: string) => void;
  color?: string;
}

const LocationSearch: React.FC<LocationSearchProps> = ({
  placeholder,
  value,
  onLocationSelect,
  color = 'blue',
}) => {
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
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          className={`w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 transition-all duration-200 focus:outline-none focus:ring-4 focus:bg-white ${borderColors[color as keyof typeof borderColors]}`}
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <IonSpinner name="crescent" className="w-4 h-4 text-gray-400" />
          </div>
        )}
      </div>
      
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-[1001] w-full bg-white mt-1 rounded-xl shadow-xl border border-gray-100 max-h-48 overflow-y-auto">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.place_id}
              onClick={() => handleSelect(suggestion)}
              className="w-full text-left px-4 py-2.5 hover:bg-blue-50 transition-colors duration-150 border-b border-gray-50 last:border-b-0"
            >
              <p className="text-sm text-gray-800 truncate">
                {suggestion.display_name.split(',').slice(0, 2).join(', ')}
              </p>
              <p className="text-xs text-gray-400 truncate">
                {suggestion.display_name.split(',').slice(2, 4).join(', ')}
              </p>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default LocationSearch;
