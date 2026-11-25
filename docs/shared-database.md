# A shared database of sequence reads (design, not built)

The goal: results from everyone who runs seqfun-annotator can be pooled in one database, and a new protein can
be searched against every annotated sequence (DIAMOND or BLAST) to find what models have said about it and its
relatives. This note records the design choices already made in the package so that pooling needs no migration,
and sketches the service. Nothing here is built yet beyond the local pieces listed under "Already in place".

## Already in place

- **Records are keyed by sequence checksum.** Every record carries `seq_md5`, the MD5 of the upper-case residues,
  the checksum UniParc uses, and the residues themselves (`sequence`). Identifiers from FASTA headers (`id`) are
  kept only as labels; they never enter a key. A shuffled control has the checksum of the shuffled sequence.
- **Every call has a stable id.** `uid` is a random UUID for a live call, and a hash of batch id and request id
  for a batch call. A reused (cached) answer keeps the uid of the call that produced it, so it is never counted
  twice.
- **Exports merge without duplicates.** `seqfun export` writes one self-contained JSON record per line;
  `seqfun import` adds records whose uid is new and skips the rest. Concatenating exports from several people and
  importing them gives the union. Two people asking the same question get two uids: both samples are kept, which
  is what a sampled model answer calls for.
- **Prompt versions are content hashes.** `prompt_version` is the first 12 hex digits of the SHA-256 of the
  task's fixed prompt text, so records from an edited prompt can never be mistaken for records of the original.
  `prompt_sha256` hashes the full prompt including the sequence.
- **Provenance travels with the record:** provider, model, served model, effort, request options, client library
  and version, seqfun version, token counts including thinking, the prompt-only token count and the
  `input_tokens_match` check, cost, stop reason, timestamps, and batch id.
- **FASTA for search.** `seqfun fasta` writes each annotated real sequence once, named by its MD5, with the ids
  and tasks it was annotated under. `diamond makedb --in annotated.fasta -d seqfun` builds a search database;
  hits join back to the records on `seq_md5`.

## The shared service (sketch)

1. **Submission.** A user uploads an export (JSONL). The service validates each line against the `Annotation`
   model, recomputes `seq_md5` from `sequence` and rejects mismatches, recomputes the checks (they are
   deterministic), and inserts by `uid`. The uploader is recorded per record.
2. **Storage.** One `calls` table, the same columns as the local store, plus `submitted_by` and
   `submitted_at`. A `sequences` table holds each distinct sequence once (`seq_md5` primary key), with length and
   any UniParc accession found for the checksum.
3. **Search.** A nightly job writes the FASTA of all sequences and rebuilds the DIAMOND database. A query
   sequence is first looked up by exact MD5, then searched with DIAMOND. Each hit lists the annotations of the hit
   sequence grouped by task, model and prompt version, with identity and coverage so a user can judge how far an
   annotation transfers.
4. **Agreement views.** For each sequence and task: how many samples, from which models, how often they agree
   (same Pfam family, same active-site call), and how often the shuffled control was clean. Agreement across
   samples is not evidence of correctness, and the views say so.
5. **Trust.** Submissions are self-reported. Flag records whose input-token check failed or that came from a
   route other than a direct API call, and let queries exclude them.

## Open questions

- Whether to store reply text for every record (useful for re-parsing; large) or only the parsed answer plus a
  hash of the text.
- Licence and attribution for pooled model outputs.
- Whether UniParc cross-references should be resolved at submission or at query time.
