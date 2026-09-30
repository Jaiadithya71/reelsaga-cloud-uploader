"""Read-only startup check. Uploading is not wired until durable state/canaries pass."""
import json
import os
from pathlib import Path
from reelqueue import validate

def main():
    path = os.environ.get('QUEUE_MANIFEST_PATH')
    if not path:
        print('Queue not connected. Offline tests only; no uploads attempted.')
        return
    data = json.loads(Path(path).read_text())
    for item in data['items']:
        validate(item, data['catalog'], 'UC71kSXnAt6Ipy7KqVVo3mdA', 'reelsaga3000')
    print(f"Validated {len(data['items'])} queue entries. No publishing performed.")

if __name__ == '__main__':
    main()
