create extension if not exists vector;

create table profiles (
    handle text primary key,
    platform text, display_name text, bio text,
    location text, followers integer, following integer,
    tweet_count integer, is_verified boolean, joined_at text,
    website text, profile_image_url text,
    raw_json jsonb, fetched_at timestamp default now()
);

create table tweets (
    id text primary key,
    handle text references profiles(handle) on delete cascade,
    text text, likes integer default 0, views integer default 0,
    retweets integer default 0, created_at text,
    embedding vector(384),
    fetched_at timestamp default now()
);

create index on tweets using ivfflat (embedding vector_cosine_ops);

create or replace function search_tweets(
    handle_filter text, query_embedding vector(384), match_count int default 5
) returns table (text text, likes integer, views integer, similarity float)
language sql stable as $$
    select text, likes, views,
           1 - (embedding <=> query_embedding) as similarity
    from tweets where handle = handle_filter
    order by embedding <=> query_embedding limit match_count;
$$;

alter table profiles disable row level security;
alter table tweets disable row level security;