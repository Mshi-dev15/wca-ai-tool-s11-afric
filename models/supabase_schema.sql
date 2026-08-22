create table farmers (
    id bigint generated always as identity primary key,
    name text not null,
    created_at timestamptz default now()
);

create table chats (
    id bigint generated always as identity primary key,
    farmer_id bigint references farmers(id) not null,
    title text,
    started_at timestamptz default now()
);

create table messages (
    id bigint generated always as identity primary key,
    chat_id bigint references chats(id) not null,
    role text not null,
    content text not null,
    intent_json text,
    created_at timestamptz default now()
);
