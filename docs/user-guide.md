# Knowledge Base — User Manual

A quick guide for **call-centre agents** and **supervisors** using the ZESCO
knowledge base.

---

## What it is

The knowledge base is a search-and-answer assistant. When a caller asks a
question you're unsure about, you type the question and get a short, grounded
answer drawn from ZESCO's own documents (policies, SOPs, tariffs, FAQs) and past
call transcripts — along with the source each answer came from.

It will **not** guess. If the information isn't in the documents, it tells you so
and suggests you escalate.

---

## Opening the app

Open your browser and go to the knowledge base address:

- Local/testing: `http://localhost:5173`
- Production: the URL provided by IT

At the bottom of the screen a status bar shows a green dot and the number of
documents loaded when the system is online. A red dot means it can't reach the
service — tell IT.

The app has three tabs at the top: **Ask**, **Search**, **Ingest**.

---

## For agents

### Asking a question (the Ask tab)

1. Click the **Ask** tab (it opens here by default).
2. Type the caller's question in plain language, e.g.
   *"How does a customer report a power outage?"*
3. Press **Enter** or click **Ask**.
4. A short answer appears, followed by **Sources** — the document(s) the answer
   came from.

Your questions and answers stay on screen as a running list, so you can scroll
back during the call.

### Reading the answer

- **The answer** is written so you can read or paraphrase it directly to the
  caller.
- **Sources** (the grey chips) tell you which document backs the answer, in case
  you need to double-check or quote a policy.
- If you see *"I don't have that information…"*, the KB has no document covering
  it — follow your normal **escalation** process.

### Tips for better answers

- Ask one thing at a time. Short, specific questions work best.
- Use the caller's actual wording if you're unsure what to ask.
- If the first answer isn't quite right, rephrase and ask again.
- Don't put personal customer details (account numbers, names) into the box —
  ask about the **process**, not the individual.

### Searching instead of asking (the Search tab)

Use **Search** when you'd rather see the raw source passages than a written
answer. Type a few keywords and you'll get the most relevant document snippets,
each with a relevance score. Useful for finding the exact wording of a policy.

---

## For supervisors — adding documents (the Ingest tab)

Keeping the knowledge base accurate means feeding it approved, up-to-date
documents. Supported file types: **.txt, .md, .pdf, .docx**.

### Upload a single document

1. Click the **Ingest** tab.
2. Under **Upload a document**, click **Choose file** and pick the file.
3. Wait for the confirmation message (e.g. *"Ingested 8 chunk(s)…"*).

The document is now searchable immediately. Uploading a newer version of the
same file replaces the old one automatically.

### Ingest a folder on the server

Under **Ingest a server path**, enter a file or folder path that the service can
reach (e.g. `/u01/kb_docs`) and click **Ingest**. Every supported file in that
folder is loaded.

### Good practice

- Only add **approved** documents — agents will quote them to callers.
- Keep master copies in one agreed folder (e.g. `/u01/kb_docs`) so the set stays
  tidy and can be re-loaded on a schedule.
- Re-upload a document whenever its policy changes; the old version is replaced.

> Removing a document from the index (when a policy is withdrawn) currently
> needs IT to run a re-sync — ask IT if you need something taken out.

---

## Frequently asked

**Why did it say it doesn't know?**
The answer isn't in any loaded document. Escalate as normal, and ask your
supervisor to add the relevant document.

**Can I trust the answer?**
The system only answers from ZESCO's documents and shows its sources. If
something looks off, check the cited source or escalate.

**It says the service is offline (red dot).**
The knowledge base service isn't reachable. Report it to IT.

**Does it store the caller's details?**
Don't type personal details. Ask about processes and policies, not individuals.

---

## Quick reference

| I want to…                         | Tab     | Action                                  |
| ---------------------------------- | ------- | --------------------------------------- |
| Get a ready-to-say answer          | Ask     | Type the question, press Enter          |
| Find the exact policy wording      | Search  | Type keywords, read the snippets        |
| Add a new/updated document         | Ingest  | Upload a file or ingest a server folder |
| Check the system is online         | —       | Green dot in the bottom status bar      |
