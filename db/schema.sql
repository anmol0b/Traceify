-- Traceify schema for Postgres + pgvector (e.g. Neon). Safe to re-run.
-- Apply with: psql "$DATABASE_URL" -f db/schema.sql

create extension if not exists vector;

create table if not exists profiles (
    handle            text primary key,
    platform          text not null default 'x',
    display_name      text,
    bio               text,
    location          text,
    followers         integer,
    following         integer,
    tweet_count       integer,
    is_verified       boolean,
    joined_at         text,
    website           text,
    profile_image_url text,
    raw_json          jsonb,
    fetched_at        timestamptz not null default now()
);

create table if not exists tweets (
    id          text primary key,
    handle      text not null references profiles(handle) on delete cascade,
    text        text not null,
    likes       integer default 0,
    views       bigint default 0,
    retweets    integer default 0,
    created_at  text,
    embedding   vector(384),
    fetched_at  timestamptz not null default now()
);

create index if not exists tweets_handle_idx on tweets (handle);
create index if not exists tweets_embedding_idx on tweets using hnsw (embedding vector_cosine_ops);
