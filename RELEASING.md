# Releasing peptalk

1. Make sure `main` is green.
2. On GitHub, [draft a new release](https://github.com/ai4curation/peptalk/releases/new). Create a new tag
   `vX.Y.Z` on `main`, give it a title and notes (copy the section from [CHANGELOG.md](CHANGELOG.md)), and
   publish it.

That's it. The `Publish Python Package` workflow (`.github/workflows/pypi-publish.yaml`) builds the package and
uploads it to [PyPI](https://pypi.org/project/peptalk-llm/) by trusted publishing, in the `release` environment. The
version comes from the tag (uv-dynamic-versioning), so nothing in the code needs editing.

PyPI trusted publisher settings: project `peptalk-llm`, owner `ai4curation`, repository `peptalk`, workflow
`pypi-publish.yaml`, environment `release`.
