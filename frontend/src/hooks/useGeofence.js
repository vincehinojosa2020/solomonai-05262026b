import { useState, useEffect, useCallback, useRef } from 'react';
import { API_URL } from '@/lib/utils';

export function useGeofence() {
  const [status, setStatus] = useState('idle'); // idle | watching | inside | outside | error | denied
  const [distance, setDistance] = useState(null);
  const [checkinResult, setCheckinResult] = useState(null);
  const watchIdRef = useRef(null);
  const checkedInRef = useRef(false);

  const checkIn = useCallback(async (lat, lon) => {
    if (checkedInRef.current) return;
    checkedInRef.current = true;

    try {
      const token = localStorage.getItem('session_token');
      const res = await fetch(`${API_URL}/portal/attendance/geofence-checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ latitude: lat, longitude: lon })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.checked_in) {
          setStatus('inside');
          setCheckinResult(data);
          return data;
        }
      }
      checkedInRef.current = false;
    } catch (err) {
      console.error('Geofence check-in error:', err);
      checkedInRef.current = false;
    }
    return null;
  }, []);

  const startWatching = useCallback(() => {
    if (!navigator.geolocation) {
      setStatus('error');
      return;
    }

    setStatus('watching');

    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        checkIn(latitude, longitude);
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setStatus('denied');
        } else {
          setStatus('error');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
    );
  }, [checkIn]);

  const stopWatching = useCallback(() => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setStatus('idle');
  }, []);

  const reset = useCallback(() => {
    checkedInRef.current = false;
    setCheckinResult(null);
    setStatus('idle');
  }, []);

  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return { status, distance, checkinResult, startWatching, stopWatching, reset };
}
