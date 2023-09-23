# ece_service_visualiser

https://datafinder.stats.govt.nz/data/?created_at.after=2023-01-13T16%3A40%3A52.957Z

user experience:
- search for my address
- map shows my address and 3 closest centres in terms of commute time
- for each centre show name, population demand


population demand for each centre is the amount of population within 30 minutes commute or 10km of an ECE service

to create population demand for each service:
- get all meshblocks within prescribed range
- calculate total population within prescribed distance for each ece service