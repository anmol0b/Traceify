-- Run once if you created the database with the original (Streamlit) schema.
-- v2 switched embeddings from all-MiniLM-L6-v2 to BAAI/bge-small-en-v1.5 (both 384-dim, but not
-- compatible), so cached tweets must be re-embedded: clearing the cache forces a refetch.
truncate tweets;
delete from profiles;

alter table profiles alter column fetched_at type timestamptz using fetched_at at time zone 'utc';
alter table tweets   alter column fetched_at type timestamptz using fetched_at at time zone 'utc';
alter table tweets   alter column views type bigint;

drop index if exists tweets_embedding_idx;
drop function if exists search_tweets(text, vector, int);
-- Now run schema.sql to create the new indexes and function, and enable RLS.
