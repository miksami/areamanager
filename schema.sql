create table users ( --uid
    id integer primary key,
    username text unique,
    passhash text
);

create table areas ( --aid
    id integer primary key,
    uid integer references users,
    name text,
    description text
);

create table items ( --pid
    id integer primary key,
    uid integer references users,
    aid integer references areas,
    name text
);

create table area_images ( --paid
    id integer primary key,
    aid integer references areas,
    image blob
);

create table prop_images ( --piid
    id integer primary key,
    iid integer references items,
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