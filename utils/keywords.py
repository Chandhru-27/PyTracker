"""
Search keywords for active video playback tracking.
"""

video_keywords = [
                # Web Browsers (may contain video/audio)
                'chrome', 'firefox', 'edge', 'opera', 'brave', 'safari', 'vivaldi', 'chromium',
                
                # Streaming Platforms
                'youtube', 'youtube music', 'netflix', 'prime video', 'disney+', 'hulu', 'hbomax', 
                'spotify', 'apple tv', 'peacock', 'paramount+', 'crunchyroll', 'funimation',
                'twitch', 'dailymotion', 'vimeo', 'tiktok', 'instagram', 'facebook watch',
                
                # Media Players (Desktop Apps)
                'vlc', 'mpv', 'potplayer', 'kodi', 'plex', 'jellyfin', 'emby', 'media player',
                'windows media player', 'quicktime', 'itunes', 'foobar2000', 'winamp', 'aimp',
                'musicbee', 'powerdvd', 'divx', 'kmplayer', 'gom player', 'smplayer', 'mx player',
                
                # Video Editing/Recording (often play media)
                'obs', 'streamlabs', 'adobe premiere', 'davinci resolve', 'final cut pro', 'filmora',
                'camtasia', 'shotcut', 'vegas pro', 'after effects', 'audacity',
                
                # Video Conferencing (often play audio/video)
                'zoom', 'teams', 'skype', 'webex', 'google meet', 'discord', 'jitsi', 'gotomeeting',
                
                # Cloud Gaming/Remote Play
                'xbox game bar', 'nvidia geforce now', 'steam link', 'parsec', 'moonlight',
                
                # Other Media-Related Apps
                'spotify', 'deezer', 'tidal', 'amazon music', 'pandora', 'soundcloud', 'vlc web plugin',
                'iina', 'elmedia player', 'infuse', 'nplayer', 'bsplayer', 'realplayer', 'arc',
                
                # File Extensions (if window titles show them)
                '.mp4', '.mkv', '.avi', '.mov', '.flv', '.webm', '.mp3', '.wav', '.m4a', '.aac',
                
                # Mobile Emulators (if running on PC)
                'bluestacks', 'nox player', 'ldplayer', 'memu', 'genymotion',
                
                # Additional Terms (partial matches)
                'video', 'movie', 'stream', 'playback', 'livestream', 'podcast', 'music', 'film'
            ]