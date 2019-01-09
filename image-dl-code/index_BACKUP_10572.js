<<<<<<< HEAD
(async function() {
  const DownloadImages = require("./DownloadImages");

  const inputFileName = "species_native_status_EOL_ID_test.csv";
  //const inputFileName = "species_native_status_EOL_ID.csv";
  const outFileName = "../data/jpgs/csv/download_files_results.csv";
  const errorFilename = "../data/jpgs/csv/download_files_error.csv";
  const pngsPath = "../data/jpgs";
  const logLevel = "all";

  // create the object with settings
  const downloadImages = new DownloadImages({
    inputFileName,
    outFileName,
    errorFilename,
    pngsPath,
    logLevel
  });

  // run it
  await downloadImages.run();

  // this code shouldn't be called until downloadImages is done.
  console.log("done");
})();
=======
const fetch = require("node-fetch");
const { parseCsv } = require("./shared");

var https = require("https");
var http = require("http");
var fs = require("fs");
var path = require("path");

const {
  HttpPicker,
  getMediaURL,
  getKabobedName,
  LogObjects
} = require("./functions");

const pngsPath = "../data/jpgs";
// species_native_status_EOL_ID_test.csv is a test file
//const inputFileName = "species_native_status_EOL_ID_test.csv";
const inputFileName = "species_native_status_EOL_ID.csv";

//("http://eol.org/api/pages/1.0.json?id={eolid}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false");

const writeStreamToFile = function(
  response,
  mediaURL,
  item,
  firstCode,
  logObjects
) {
  const ext = path.extname(mediaURL);
  const ourFileName = `${pngsPath}/${getKabobedName(
    item.botanical_name
  )}${ext}`;
  logObjects.log({
    ...item,
    responseCode: 200,
    firstCode,
    mediaURL,
    writtenFile: ourFileName,
    error: ""
  });
  var file = fs.createWriteStream(ourFileName);
  return response.pipe(file);
};

const writeOtherToFile = function(response, item, firstCode, logObjects) {
  const ourFileName = `${pngsPath}/other/${getKabobedName(
    item.botanical_name
  )}_${response.statusCode}.html`;
  logObjects.log({
    ...item,
    responseCode: response.statusCode,
    firstCode,
    mediaURL: response.headers.location,
    writtenFile: ourFileName,
    error: ""
  });
  var file = fs.createWriteStream(ourFileName);
  return response.pipe(file);
};

const writeImageFile = function(mediaURL, item, httpPicker, logObjects) {
  // Do we want to use EOL_ID or botanical_name to name the jpg files?
  return httpPicker.gethttp(mediaURL).get(mediaURL, function(response) {
    switch (response.statusCode) {
      case 200: {
        return writeStreamToFile(response, mediaURL, item, "", logObjects);
      }
      case 301:
      case 302: {
        // The HTTP response status code 302 Found is a common way of performing URL redirection.
        // Make 1 attempt at getting redirected resource
        // The redirected resource is in headers.location
        const {
          headers: { location }
        } = response;
        return httpPicker.gethttp(location).get(location, function(response2) {
          if (response2.statusCode == 200) {
            return writeStreamToFile(
              response2,
              mediaURL,
              item,
              response.statusCode,
              logObjects
            );
          }
          return writeOtherToFile(
            response2,
            item,
            response.statusCode,
            logObjects
          );
        });
      }
      default: {
        // All other codes
        return writeOtherToFile(
          response,
          item,
          response.statusCode,
          logObjects
        );
      }
    }
  });
};

const ensureDirectories = function(basePath) {
  if (!fs.existsSync(basePath)) {
    fs.mkdirSync(basePath);
  }
  if (!fs.existsSync(`${basePath}/other`)) {
    fs.mkdirSync(`${basePath}/other`);
  }
};

const makeFetchUrl = function(EolId) {
  return `http://eol.org/api/pages/1.0.json?id=${EolId}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`;
};

const later = function(delay) {
  return new Promise(function(resolve) {
    setTimeout(resolve, delay);
  });
};

const httpPicker = new HttpPicker(http, https);

ensureDirectories(pngsPath);

const logObjects = new LogObjects();

const list = parseCsv(inputFileName);
let status;
let wait = 0;
list.map(item => {
  if (item.EOL_ID) {
    let mediaURL = "";
    // To slow things down, wait for n * 100 miliseconds for each item in the list
    // If I don't slow things down, I get 502 errors.
    wait++;
    later(wait * 100)
      .then(() => {
        return fetch(makeFetchUrl(item.EOL_ID));
      })
      .then(response => {
        status = response.status;
        if (status === 200) {
          return response.json();
        }
        throw new Error(
          `status: ${status}; EOL_ID: ${item.EOL_ID}; URL: ${makeFetchUrl(
            item.EOL_ID
          )}`
        );
      })
      .then(json => {
        mediaURL = getMediaURL(json);
        if (mediaURL) {
          return writeImageFile(mediaURL, item, httpPicker, logObjects);
        }
        throw new Error(`No mediaURL for EOL_ID ${item.EOL_ID} `);
      })
      .catch(err => {
        logObjects.log({
          ...item,
          responseCode: status,
          firstCode: "",
          mediaURL,
          writtenFile: "",
          error: err.message
        });
      });
  } else {
    logObjects.log({
      ...item,
      responseCode: status,
      firstCode: "",
      mediaURL: "",
      writtenFile: "",
      error: "No EOL Id"
    });
  }
});
>>>>>>> Public-Tree-Map/master
