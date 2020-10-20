CREATE TABLE IF NOT EXISTS authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),    
    firstname VARCHAR(45) NOT NULL,
    lastname VARCHAR(45) NOT NULL,
    username VARCHAR(45) UNIQUE
);


CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),    
    title VARCHAR(45) NOT NULL,
    txt VARCHAR(516),
    author_id UUID NOT NULL,
    FOREIGN KEY (author_id) REFERENCES authors (id)
);


class Author(Base):
	__tablename__ = "author"

	id = Column(UUID, primary_key=True)
	firstname = Column(VARCHAR(45), nullable=False)
	lastname = Column(VARCHAR(45), nullable=False)

class Article():
	__tablename__ = "article"

	id = Column(UUID, primary_key=True #gen_random_uuid?)
	title = Column(VARCHAR(45), nullable=False)
	txt = Column(VARCHAR(516))
	author_id = Column(UUID, nullable=False, ForeignKey("authors.id"))
