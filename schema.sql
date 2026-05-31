create table users ( --uid
    id integer primary key,
    username text unique,
    passhash text
);

create table areas ( --aid
    id integer primary key,
    uid integer references users,
    name text,
    description text,
    image blob
);

create table items ( --pid
    id integer primary key,
    uid integer references users,
    aid integer references areas,
    name text,
    image blob
);

create table tags ( --tid
    id integer primary key,
    value text
);

create table area_tags ( --atid
    id integer primary key,
    aid integer references areas,
    value text
)