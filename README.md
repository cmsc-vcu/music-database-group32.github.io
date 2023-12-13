---
date: 12/12/2023
author: Rachel Farzan, Javeria Hanif, Feyza Sakin
format:
    html:
        theme: cosmo
        toc: true
        embed-resources: true
---
# Music Database 

## Description

This final report serves as an extension to deliverable 4. It covers everything about our project, from the beginning to the end. It includes important things like the project description, analysis of the problem, diagrams, schemas, notes on normalization, queries, sample data, API definition, SQL code, thoughts about the future, what the team thinks, and links to GitHub, videos, HTML, and more.

### Phase 4 Notes 

The following has ER diagrams in Chen and Crow’s foot with design notes, relational schemas, functional dependencies, normalization notes, queries, and sample data for a music database.

We represent different perspectives in Chen and Crow’s foot notations with relation sets. For Chen, rectangles are entities, ovals are attributes, and diamonds are relationships. For relationships in Chen, we represent one-to-one as “1,” zero-to-many as “0…n,” one-to-many as “1...n,” and zero-to-one as “0…1”. For Crow’s foot, each entity has its own table and we can define attributes as primary keys by writing “PK” and foreign keys as “FK.” Also, we can learn the participation and cardinality between entity relationships. While the inner symbols represent participation, the outer symbols are used for cardinality. For participation, “|” is used for total and “o” is used for partial. For cardinality, “{” and “}” are used for many, “|” is used for one, and “o” is used for zero. To render ER diagrams, "dot" is added to the start of Chen and "mermaid" is added to the start of Crow's foot notation codes while "```" is added to the end of both codes.

In the design notes, trade-offs for diagrams are discussed.

In relational schemas, each entity is specified with its attributes. If an attribute is “NOT_NULL,” “FK,” “PK,” and/or “UNIQUE,” it’s specified. “NOT_NULL” for an attribute means that we have to have a value for that attribute. For relationship tables, each foreign key reference is specified.

A functional dependency is when an attribute or attributes are dependent on another attribute/s. For example in our Music Database, the USER.ID is the determinant of user_name, password, and account_type since each user will have their own name, password, and account type that are collectively identified with the user ID. It’s the same case for ARTIST.ID, SONG.ID, ALBUM.ID, and PLAYLIST.ID, ARTIST_SONG.ID, ARTIST_ALBUM.ID, PLAYLIST_SONG.ID, and FOLLOWING.ID.

In the Normalization Notes, how the relations are in BCNF/4NF form is discussed.

In the queries, 20 queries are listed using the relational algebra. According to relational algebra, sigma (σ) is used for picking rows, pi (𝜋) is for picking columns, join (bowtie ⋈) is for connecting two tables, “COUNT(*)” is for counting, “MIN(value)” is for finding the minimum, and “MAX(value)” is for finding the maximum. When we use pi and/or sigma, we need to specify the entity (table) like this “ σ_row = value (table name) “ or “ 𝜋_column(table name) “. When we use joins, we need to set the same keys to each other like this “ ⋈ ALBUM.user_ID = USER.ID ” where both ALBUM and USER entities are comparing their user IDs.

In the sample data, tables for each relation are put with sample values. The tables’ names are user, artist, song, album, playlist, artist_song, artist_album, playlist_song, and following. 

To render the Deliverable4.qmd file into Deliverable4.html file, “quarto render Deliverable4.qmd --to html” is used.

### Videos

[Deliverable 3 Video](https://vcu.mediaspace.kaltura.com/media/Project+Deliverable+3+-+Version+2/1_thnnkrtm)

[Deliverable 4 Video](https://vcu.mediaspace.kaltura.com/media/Project+Deliverable+4/1_xyo18fcy)

[Deliverable 7 Video](https://vcu.mediaspace.kaltura.com/media/Deliverable+7/1_nwcbdq5x)

### HTML Documents

[Deliverable 4 HTML](https://github.com/cmsc-vcu/cmsc508-fa2023-prj-music-database-group32/blob/main/reports/Deliverable4.html)

[Deliverable 7 HTML](https://github.com/cmsc-vcu/cmsc508-fa2023-prj-music-database-group32/blob/main/reports/Deliverable7.html)
