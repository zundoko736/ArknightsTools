### Generated using AI. Proceed with caution.

## Local web search

Run `python web_server.py` from this repository, then open
`http://127.0.0.1:8000`. The app searches `.txt` files in `exported/`
automatically, using the same matching behavior as `search.py`. The server
listens only on this computer and does not upload or copy the text files.

The static page can also be hosted on GitHub Pages, but Pages cannot access the
Python API. To prepare the static search data, run
`python build_exported_manifest.py` and publish `index.html`, `styles.css`,
`search.js`, `exported-manifest.json`, `exported-corpus.json.gz`, and the
`exported/` folder from the root.
Then select that branch and root folder in **Settings → Pages**. The browser
fetches one compressed corpus file on the first search, then searches it in
memory. Regenerate the manifest and compressed corpus whenever the exported
text files change.