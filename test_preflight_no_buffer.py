"""Static guard: release_preflight must not call the Buffer API directly.
Buffer is under a saved provider cooldown (buffer-api-cooldown.json); the
preflight must fail closed or use the live owner-profile endpoint instead."""
import re, pathlib
def test_no_direct_buffer_calls():
    src = pathlib.Path('release_preflight.py').read_text()
    assert 'api.buffer.com' not in src, 'direct Buffer API call in preflight'
    assert not re.search(r'buffer.*fallback|fallback.*buffer', src, re.I), 'buffer fallback path present'
if __name__ == '__main__':
    test_no_direct_buffer_calls(); print('PASS: preflight has no Buffer path')
