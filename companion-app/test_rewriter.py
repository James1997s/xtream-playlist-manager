import re

sample = '''#EXTM3U\n#EXTINF:-1 tvg-name="One",One\nhttp://old.example/live/olduser/oldpass/1.m3u8\n#EXTINF:-1,Movie\nhttps://old.example/movie/olduser/oldpass/2.mp4\n#EXTINF:-1,Episode\nhttps://old.example/series/olduser/oldpass/3.mkv\n#EXTINF:-1,Other\nhttps://example.org/file.m3u8\n'''
pattern = re.compile(r'(?i)(https?://)[^/\s]+/(live|movie|series)/[^/\s]+/[^/\s]+/')
result, count = pattern.subn(r'\1new.example/$2/new%20user/new%2Fpass/', sample)
assert count == 3
assert 'olduser' not in result and 'oldpass' not in result
assert 'https://example.org/file.m3u8' in result
assert result.count('new.example') == 3
print('playlist rewrite test passed:', count)
