# peptalk 

The files peptalk reads and writes for exchange: claims files (claims about proteins, one question each) and annotation records (one model call with its answer, provenance, checks and cost; the rows of the SQLite store, of JSONL and Parquet exports, and of a future shared database). This schema is the single source of truth: peptalk/datamodel/peptalk.py (Pydantic) and the JSON Schemas next to it are generated from it with `just gen-schema`. Answer shapes of individual tasks are defined by their templates, not here.

URI: https://w3id.org/ai4curation/peptalk