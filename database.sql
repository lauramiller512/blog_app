CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firstname VARCHAR(45) NOT NULL,
    lastname VARCHAR(45) NOT NULL,
    username VARCHAR(45) UNIQUE
);


CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(45) NOT NULL,
    text VARCHAR(516) NOT NULL,
    author_id UUID NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors (id)
);
