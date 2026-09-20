# server/sites.py
# Список сайтов для проверки username.
# Формат: (имя, шаблон URL, коды "найден", коды "не найден")

USERNAME_SITES = [
    # --- существующие 20 ---
    ("GitHub",          "https://github.com/{u}",                        [200], [404]),
    ("Reddit",          "https://www.reddit.com/user/{u}/about.json",    [200], [404]),
    ("Telegram",        "https://t.me/{u}",                              [200], [404]),
    ("VK",              "https://vk.com/{u}",                            [200], [404]),
    ("Twitter/X",       "https://x.com/{u}",                             [200], [404]),
    ("Instagram",       "https://www.instagram.com/{u}/",                [200], [404]),
    ("YouTube",         "https://www.youtube.com/@{u}",                  [200], [404]),
    ("Twitch",          "https://www.twitch.tv/{u}",                     [200], [404]),
    ("Steam",           "https://steamcommunity.com/id/{u}",             [200], [404]),
    ("Pinterest",       "https://www.pinterest.com/{u}/",                [200], [404]),
    ("Medium",          "https://medium.com/@{u}",                       [200], [404]),
    ("Dev.to",          "https://dev.to/{u}",                            [200], [404]),
    ("Habr",            "https://habr.com/ru/users/{u}/",                [200], [404]),
    ("Pikabu",          "https://pikabu.ru/@{u}",                        [200], [404]),
    ("SoundCloud",      "https://soundcloud.com/{u}",                    [200], [404]),
    ("GitLab",          "https://gitlab.com/{u}",                        [200], [404]),
    ("Keybase",         "https://keybase.io/{u}",                        [200], [404]),
    ("Mastodon.social", "https://mastodon.social/@{u}",                  [200], [404]),
    ("Bluesky",         "https://bsky.app/profile/{u}",                  [200], [404]),
    ("Gravatar",        "https://gravatar.com/{u}",                      [200], [404]),

    # --- новые 15 ---
    ("TikTok",          "https://www.tiktok.com/@{u}",                   [200], [404]),
    ("Flickr",          "https://www.flickr.com/people/{u}",             [200], [404]),
    ("Spotify",         "https://open.spotify.com/user/{u}",             [200], [404]),
    ("Behance",         "https://www.behance.net/{u}",                   [200], [404]),
    ("Dribbble",        "https://dribbble.com/{u}",                      [200], [404]),
    ("Roblox",          "https://www.roblox.com/user.aspx?username={u}", [200], [404]),
    ("Duolingo",        "https://www.duolingo.com/profile/{u}",          [200], [404]),
    ("Strava",          "https://www.strava.com/athletes/{u}",           [200], [404]),
    ("Imgur",           "https://imgur.com/user/{u}",                    [200], [404]),
    ("Pastebin",        "https://pastebin.com/u/{u}",                    [200], [404]),
    ("HackerNews",      "https://news.ycombinator.com/user?id={u}",      [200], [404]),
    ("BitBucket",       "https://bitbucket.org/{u}/",                    [200], [404]),
    ("Patreon",         "https://www.patreon.com/{u}",                   [200], [404]),
    ("Tumblr",          "https://{u}.tumblr.com",                        [200], [404]),
    ("Replit",          "https://replit.com/@{u}",                       [200], [404]),
]

# Типы задач, которые разворачиваются в подзадачи http_check
COMPOSITE_MODULES = {
    "username": USERNAME_SITES,
}