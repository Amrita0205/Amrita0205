# fonts/

JetBrains Mono (SIL OFL 1.1 — see `LICENSE.txt`), subsetted so every SVG
that needs a custom typeface can embed it inline as base64 without
shipping a multi-megabyte font file.

| file | covers | used by |
|---|---|---|
| `ramp.woff2` / `.b64` | the ~20 characters in the portrait's density ramp | `generate_portrait.py` |
| `text-regular.woff2` / `.b64` | basic latin + punctuation, regular weight | `generate_stats.py`, `generate_headings.py` |
| `text-bold.woff2` / `.b64` | same, bold weight | `generate_stats.py`, `generate_headings.py` |

The `.b64` files are what the scripts actually read at generation time
(`fonts/<name>.b64`) — keep them in sync with the `.woff2` files if you
resubset.

To regenerate after changing which characters are needed:

```bash
pip install fonttools brotli
fonttools subset JetBrainsMono-Regular.ttf --text='<characters>' \
  --flavor=woff2 --layout-features='' --no-hinting -o ramp.woff2
python3 -c "import base64; open('ramp.b64','w').write(base64.b64encode(open('ramp.woff2','rb').read()).decode())"
```
