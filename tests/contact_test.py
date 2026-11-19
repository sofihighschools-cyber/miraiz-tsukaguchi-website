"""Exercise the real PHP endpoint with an isolated, fake mail transport."""
import email
import http.cookiejar
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
    folder = Path(tmp)
    transport = folder / 'sendmail'
    transport.write_text('''#!/usr/bin/env python3
import os, sys
from pathlib import Path
p = Path(os.environ['CONTACT_TEST_DIR'])
body = sys.stdin.buffer.read()
if (p / 'fail').exists():
    sys.exit(1)
with (p / 'messages').open('ab') as f:
    f.write(body + b'\\n===END===\\n')
''')
    transport.chmod(0o700)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = dict(os.environ, CONTACT_TEST_DIR=tmp)
    command = ['php', '-d', f'sendmail_path={transport}', '-d', f'sys_temp_dir={tmp}',
               '-d', f'session.save_path={tmp}', '-S', f'127.0.0.1:{port}', '-t', str(ROOT)]
    server = subprocess.Popen(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    url = f'http://127.0.0.1:{port}/contact.php'

    def request(data=None, origin=None, method=None):
        headers = {'Origin': origin} if origin else {}
        encoded = urllib.parse.urlencode(data, doseq=True).encode() if data is not None else None
        req = urllib.request.Request(url, data=encoded, headers=headers, method=method)
        try:
            response = client.open(req, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        return response.status, json.loads(response.read())

    try:
        for _ in range(50):
            try:
                status, session = request()
                break
            except urllib.error.URLError:
                time.sleep(.1)
        else:
            raise AssertionError('PHP server did not start')
        assert status == 200 and len(session['token']) == 64
        valid = {'token': session['token'], 'name': 'テスト保護者', 'role': '保護者',
                 'grade': '小学1年', 'tel': '090-0000-0000', 'email': 'parent@example.com',
                 'purpose[]': ['見学したい', '体験したい'], 'message': 'テスト本文\n2行目です。', 'agree': 'on'}
        assert request(method='PUT')[0] == 405
        assert request(valid, origin='https://example.com')[0] == 403
        assert request({**valid, 'token': 'bad'})[0] == 403
        for change in ({'name': ''}, {'role': 'invalid'}, {'agree': ''}, {'purpose[]': []},
                       {'purpose[]': ['invalid']}, {'email': 'x@example.com\r\nBcc: attacker@example.com'},
                       {'website': 'spam'}, {'message': 'x' * 15001}, {'tel': 'invalid'}, {'name[]': 'x', 'name': []}):
            assert request({**valid, **change})[0] == 422, change
        assert not (folder / 'messages').exists(), 'Invalid requests must never send mail'
        assert request(valid) == (200, {'ok': True})
        assert request(valid) == (200, {'ok': True}), 'Safe retry should succeed'
        messages = (folder / 'messages').read_bytes().split(b'\n===END===\n')
        assert len(messages) == 2, 'Safe retry must not send a second message'
        parsed = email.message_from_bytes(messages[0])
        assert parsed['To'] == 'contact@sofi-school.com'
        assert parsed['Reply-To'] == 'parent@example.com'
        body = parsed.get_payload(decode=True).decode('utf-8')
        assert '見学したい、体験したい' in body and 'テスト本文\n2行目です。' in body
        assert request({**valid, 'email': '', 'message': 'メール未入力'})[0] == 200
        (folder / 'fail').touch()
        assert request({**valid, 'message': '配送障害'})[0] == 503
        (folder / 'fail').unlink()
        assert request({**valid, 'message': '配送障害'})[0] == 200, 'Failed sends must be retryable'
        assert request({**valid, 'message': '5回目'})[0] == 200
        assert request({**valid, 'message': '6回目'})[0] == 429
        print('PASS: validation, CSRF, origin, UTF-8 mail, optional email, duplicate prevention, failures, rate limit')
    finally:
        server.terminate()
        server.wait(timeout=5)
