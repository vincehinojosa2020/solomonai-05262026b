import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';

export default function MusicPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.3);
  const audioRef = useRef(null);

  // YouTube audio URL - using a worship ambient track
  const audioSrc = "https://www.youtube.com/embed/Lm8ryOxXack?autoplay=0&enablejsapi=1";

  useEffect(() => {
    // Create audio element for background music
    const audio = new Audio();
    audio.loop = true;
    audio.volume = volume;
    audioRef.current = audio;

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const togglePlay = () => {
    if (isPlaying) {
      // Pause
      setIsPlaying(false);
    } else {
      // Play
      setIsPlaying(true);
    }
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  return (
    <>
      {/* Hidden YouTube iframe for audio */}
      {isPlaying && (
        <iframe
          style={{ display: 'none' }}
          src={`https://www.youtube.com/embed/Lm8ryOxXack?autoplay=1&loop=1&playlist=Lm8ryOxXack`}
          allow="autoplay"
          title="Background Music"
        />
      )}
      
      <div className="music-player" data-testid="music-player">
        <button 
          className="music-player-btn"
          onClick={togglePlay}
          data-testid="music-play-btn"
          aria-label={isPlaying ? 'Pause music' : 'Play music'}
        >
          {isPlaying ? (
            <Pause className="w-4 h-4" />
          ) : (
            <Play className="w-4 h-4 ml-0.5" />
          )}
        </button>
        
        <div className="music-player-info">
          <div className="music-player-title">Ambient Worship</div>
          <div className="music-player-artist">Background Music</div>
        </div>

        <button 
          className="music-player-btn"
          onClick={toggleMute}
          data-testid="music-mute-btn"
          aria-label={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? (
            <VolumeX className="w-4 h-4" />
          ) : (
            <Volume2 className="w-4 h-4" />
          )}
        </button>

        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={volume}
          onChange={handleVolumeChange}
          className="volume-slider"
          data-testid="music-volume"
          aria-label="Volume"
        />
      </div>
    </>
  );
}
