# Area Manager

## Functionality
- This is software for managing areas. Areas have a name, description, image, and tags.
- User can create an account and use it to log in to the software.
- User can add areas and edit areas and delete them.
- User can see areas added to the software.
- User can search areas by keyword and/or tags.
- Userpage shows how many areas the user has added, and a list of the areas.
- User can tag areas by vibe (ex. normal, silly, cool, weird, dangerous, curious).
- User can add items to the area, by uploading an image. The area lists what items have been added to it.

The primary content type is areas, and the secondary content type is items.

## How to run

1. Install `flask`:  
```
$ pip install flask
```
2. Create database:  
```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```
3. Run:  
```
$ flask run
```

## Notes

As of the current commit:

- User can create an account, and log in
- User can create, edit, and delete areas
- Area listing lists all areas, and allows searching by a keyword (with the ability to only search name, description, and author name), and to filter by a vibe
- Userpage shows how many areas the user has added, and a list of the areas.
- User can add items to areas, and edit and delete them.
- Areas can be tagged with multiple vibes