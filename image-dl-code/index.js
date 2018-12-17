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
const inputFileName = "species_native_status_EOL_ID_test.csv";
//const inputFileName = "species_native_status_EOL_ID.csv";

//("http://eol.org/api/pages/1.0.json?id={eolid}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false");

const writeStreamToFile = function(response, mediaURL, item, logObjects) {
  const ext = path.extname(mediaURL);
  const ourFileName = `${pngsPath}/${getKabobedName(
    item.botanical_name
  )}${ext}`;
  logObjects.log({
    ...item,
    responseCode: 200,
    mediaURL,
    writtenFile: ourFileName,
    error: ""
  });
  var file = fs.createWriteStream(ourFileName);
  return response.pipe(file);
};

const writeOtherToFile = function(response, item, logObjects) {
  const ourFileName = `${pngsPath}/other/${getKabobedName(
    item.botanical_name
  )}_${response.statusCode}.html`;
  logObjects.log({
    ...item,
    responseCode: response.statusCode,
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
        return writeStreamToFile(response, mediaURL, item, logObjects);
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
            return writeStreamToFile(response2, mediaURL, item, logObjects);
          }
          return writeOtherToFile(response2, item, logObjects);
        });
      }
      default: {
        // All other codes
        return writeOtherToFile(response, item, logObjects);
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

const httpPicker = new HttpPicker(http, https);

ensureDirectories(pngsPath);

const logObjects = new LogObjects();

const list = parseCsv(inputFileName);
list.map(item => {
  if (item.EOL_ID) {
    let mediaURL = "";
    fetch(
      `http://eol.org/api/pages/1.0.json?id=${
        item.EOL_ID
      }&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false`
    )
      .then(response => response.json())
      .then(json => {
        mediaURL = getMediaURL(json);
        if (mediaURL) {
          return writeImageFile(mediaURL, item, httpPicker, logObjects);
        }
      })
      .catch(err =>
        logObjects.log({
          ...item,
          responseCode: "",
          mediaURL: "",
          writtenFile: "",
          error: err.message
        })
      );
  } else {
    logObjects.log({
      ...item,
      responseCode: "",
      mediaURL: "",
      writtenFile: "",
      error: ""
    });
  }
});
