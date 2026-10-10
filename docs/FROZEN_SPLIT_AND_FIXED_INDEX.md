# Frozen evaluation split and fixed neural index
The 40-item team-reviewed worksheet is frozen using seed 633 into **24 dev and 16 sealed test** records, stratified by the six course categories. The public manifest contains only IDs/hashes. All answer labels remain in a private ZIP; do not commit them to this public repo or evaluate on the test split until final baseline configurations are frozen.

The team attested individual self-review dated October 10, 2026. Original questions were AI-assisted; this does not establish independent student-authored creation before chatbot development.

The GitHub Actions fixed-index workflow downloads verified CDC crawl run 38016315533 (163 normalized pages, 35 PDFs, 13 table pages), audits its raw hashes, creates 180-word windows with 30-word overlap, builds all-MiniLM-L6-v2 384-d L2-normalized embeddings in Chroma/cosine, measures actual model token counts, validates no orphan IDs, and archives the build. Run the 24-item development benchmark only after downloading its index artifact. The hosted Render demo does not use this index yet.
