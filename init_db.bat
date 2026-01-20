@echo off
echo Initializing database with SQL script...
sqlite3 news.db < init_db.sql
echo Database initialized successfully!
pause
