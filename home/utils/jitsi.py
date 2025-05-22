# home/utils/jitsi.py

import jwt
import time

def generate_jitsi_jwt(user, room_name):
    app_id = "your_app_id"
    app_secret = "your_app_secret"
    domain = "your.jitsi.server.com"

    payload = {
        "aud": app_id,
        "iss": app_id,
        "sub": domain,
        "room": room_name,
        "exp": int(time.time()) + 3600,
        "context": {
            "user": {
                "name": user.get_full_name(),
                "email": user.email,
                "avatar": f"https://yourdomain.com/avatar/{user.id}.png"
            }
        }
    }

    return jwt.encode(payload, app_secret, algorithm="HS256")
