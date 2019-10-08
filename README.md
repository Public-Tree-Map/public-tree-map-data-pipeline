# public-tree-data

Public Tree Map uses open datasets to document publicly owned park + street + landmark trees in Santa Monica, California. Please see below for more information about the data sources and project.

## Running the Pipeline Locally

Prerequisites:
- `make`
- `node`

After a fresh clone, run `npm install` to install the necessary node modules.

To run the full pipeline, which will download the latest tree data and all
images, run:

```bash
make release
```

To skip lengthy network requests, you can run a smaller version of the pipeline
with:

```bash
make local-only
```

See the `Makefile` for other rules that are available.

## Using Docker (the easy way)

Prerequisites:
- docker
- docker-compose

```bash
docker-compose build
```

This should build two docker images:
- `public-tree-map-python:latest`
- `public-tree-map-node:latest`

As above, if you wish to run the full pipeline, which will download the latest tree data and all
images, then run:

```bash
make release-docker
```

To skip the lengthy network requests, you can run a smaller version of the pipeline
(using docker) with:

```bash
make local-only-docker
```

See the `Makefile` for other rules that are available.

### Viewing the Logs

The various scripts that makeup the pipeline rely on reading/writing to stdin 
and stdout, so the scripts can't log to stdout like you'd expect. Instead, they
write to a log file that's located at tmp/log.txt. If you'd like to watch logs
as they happen, simply run:

```bash
tail -f tmp/log.txt
```

### General Thoughts on the Pipeline

We don't want a server. To avoid this, we serve static data as JSON via a Google 
Cloud bucket. This has a number of benefits, namely cost and client simplicity.

The pipeline in general works like this:

- Start with tree data provided by Santa Monica.
- End with one JSON file that can be used to render the map, and a series of 
  JSON files that represent the details of each individual tree.
- In between, we break down each augmentation/alteration of the data into a
  series of distinct processes, each of which reads from stdin and writes to
  stdout. Examples include doing the initial parse of the CSV, and finding
  images for each tree.
- Each of these scripts are written and documented extensively.
- The Makefile composes these scripts into a set of routines.
- CircleCI will run the `make release` script nightly to update the data.

## Protocol for pull requests + code review

- Please review open issues and link your pull request to the relevant issue.
- Please create new branch!
- In your pull request, please list and explain all proposed changes to the code base (additions, deletions). If you reuse code from elsewhere, please make sure you've attributed it.
- Please apply all relevant labels to your pull request.
- Please request a review (either from a specific person or from the slack channel).
- Reviewers: please review all proposed changes, write comments and questions in line notes. Please review all updates made at your request.
- Reviewer and requester: please confirm with each other that the PR is ready to merge. Please make sure that the PR branch name documents the new changes.

## Data Sources
- [Biodiversity Heritage Library - API documentation](https://www.biodiversitylibrary.org/api2/docs/docs.html)
- [Calflora](http://www.calflora.org/)
- [California Invasive Plant Council](http://www.cal-ipc.org/plants/inventory/)
- [Canopy Tree Library](https://canopy.org/tree-info/canopy-tree-library/)
- [Encyclopedia of Life (EOL) - API documentation](http://eol.org/api)
- [Google Street View - API documentation](https://developers.google.com/maps/documentation/streetview/)
- [iNaturalist - API documentation](https://www.inaturalist.org/pages/api+reference)
- [Implementing and managing urban forests: A much needed conservation strategy to increase ecosystem services and urban wellbeing - open access PDF](https://www.sciencedirect.com/science/article/pii/S0304380017300960?via%3Dihub)
- [IUCN Red List of Threatened Species - API documentation](http://apiv3.iucnredlist.org/)
- [The Jepson Herbarium eFlora](http://ucjeps.berkeley.edu/eflora/)
- [LA City - Urban Forestry Division - Street Tree Selection Guide (Bureau of Street Services)](http://bss.lacity.org/urbanforestry/streettreeselectionguide.htm)
- [LA Times' Neighborhood Profile](http://maps.latimes.com/neighborhoods/neighborhood/santa-monica/)
- [Missouri Botanical Garden - Plant Finder](http://www.missouribotanicalgarden.org/plantfinder/plantfindersearch.aspx)
- [The Plant List](http://www.theplantlist.org/)
- [Santa Monica - Open Data - Neighborhood Organization Boundaries](https://data.smgov.net/Public-Assets/Neighborhood-Organization-Boundaries/juzu-tcbz/data)
- [Santa Monica - Open Data - Trees](https://data.smgov.net/Public-Assets/Trees/ekya-mi9c)
- [Santa Monica - Open Data - Trees Inventory](https://data.smgov.net/Public-Assets/Trees-Inventory/w8ue-6cnd)
- [Santa Monica - Urban Forest - Heritage Trees](https://www.smgov.net/Portals/UrbanForest/content.aspx?id=53687092939)
- [Santa Monica - Urban Forest - Landmark Trees](https://www.smgov.net/Portals/UrbanForest/content.aspx?id=53687091867)
- [Santa Monica - Urban Forest - Watering Frequencies for Mature Trees PDF (pp9-13)](https://www.smgov.net/uploadedFiles/Portals/UrbanForest/FINAL%20Trees%20Watering%20Guidelines.pdf)
- [Santa Monica - Urban Forest - Watering Street Trees in Santa Monica - Water Requirements by Species PDF (pp13-19)](https://www.smgov.net/uploadedFiles/Portals/UrbanForest/Maintenance/WateringStreetTrees.pdf)
- [SelecTree - CalPoly](https://selectree.calpoly.edu/)
- [Theodore Payne Foundation - California Native Plant Database](http://www.theodorepayne.org/mediawiki/index.php?title=California_Native_Plant_Library)

## Tree attributes and current sources
- [List of attribute fields and views for our application - gist](https://gist.github.com/Reltre/6554dfc430986803553d84742f1b88a9)
- Initial views (desktop):
  - 1 - no tree selected (home/map view)
  - 2 - native CFP tree species view
  - 3 - non-native tree species view
  - 4 - Washingtonia filifera (only native CFP palm species) view
  - 5 - non-native palm species view
  - 6 - tree family view
- Species Imagery - [Encyclopedia of Life](http://eol.org/api)
- CA Native status - [Calflora.org](www.calflora.org) and [Theodore Payne Foundation](http://www.theodorepayne.org/mediawiki/index.php?title=California_Native_Plant_Library)
- Nearest Address, GPS Coordinates, Height Range, Trunk Diameter (DBH) Range, Tree ID - [Trees Inventory - Santa Monica Open Data](https://data.smgov.net/Public-Assets/Trees-Inventory/w8ue-6cnd)
- Geographic Range description (countries occurrence), IUCN Red List Status - [IUCN Red List API - v3](http://apiv3.iucnredlist.org/)
- Recommended Watering Frequency - [City of Santa Monica Public Works Department PDF (pp9-13)](https://www.smgov.net/uploadedFiles/Portals/UrbanForest/FINAL%20Trees%20Watering%20Guidelines.pdf)
- Species Growth, Shade Production, Shedability, Spread, Trunk clearnance - [Canopy Tree Library](https://canopy.org/tree-info/canopy-tree-library/)
- Street View Imagery - [Google Street View](https://developers.google.com/maps/documentation/streetview/)
- For CA native species:
- Species Height by Width, Native Distribution, Native Habitat - [Theodore Payne Foundation](http://www.theodorepayne.org/mediawiki/index.php?title=California_Native_Plant_Library)
- For non-native tree species:
- Invasive Status - [California Invasive Plant Council](https://www.cal-ipc.org/plants/inventory/)
- Our public [google drive folder](https://drive.google.com/drive/u/1/folders/1PfSpH5yuydJEK-sD-PPTXcj9jHA6QLi4)
