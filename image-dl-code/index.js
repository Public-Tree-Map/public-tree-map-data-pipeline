const fetch = require("node-fetch");
const { parseCsv } = require("./shared");

var https = require("https");
var http = require("http");
var fs = require("fs");
var path = require("path");

const { HttpPicker, getMediaURL, getKabobedName } = require("./functions");

const pngsPath = "../data/jpgs";
// species_native_status_EOL_ID_test.csv is a test file
const inputFileName = "species_native_status_EOL_ID_test.csv";
//const inputFileName = "species_native_status_EOL_ID.csv";

//("http://eol.org/api/pages/1.0.json?id={eolid}&images_per_page=1&videos_per_page=0&sounds_per_page=0&maps_per_page=0&texts_per_page=0&details=true&taxonomy=false");

const writeImageFile = function(mediaURL, botanical_name, httpPicker, fs) {
  if (!fs.existsSync(pngsPath)) {
    fs.mkdirSync(pngsPath);
  }
  if (!fs.existsSync(`${pngsPath}/302`)) {
    fs.mkdirSync(`${pngsPath}/302`);
  }
  if (!fs.existsSync(`${pngsPath}/other`)) {
    fs.mkdirSync(`${pngsPath}/other`);
  }
  // Do we want to use EOL_ID or botanical_name to name the jpg files?
  return httpPicker.gethttp(mediaURL).get(mediaURL, function(response) {
    //console.log({ code: response.statusCode });
    switch (response.statusCode) {
      case 200: {
        const ext = path.extname(mediaURL);
        const ourFileName = `${pngsPath}/${getKabobedName(
          botanical_name
        )}${ext}`;
        var file = fs.createWriteStream(ourFileName);
        response.pipe(file);
        break;
      }
      case 302: {
        // The HTTP response status code 302 Found is a common way of performing URL redirection.
        // All appear to have a valid link in an HTML page.
        console.log(`MOVED -- ${botanical_name}  -- not logged`);
        const ourFileName = `${pngsPath}/302/${getKabobedName(
          botanical_name
        )}.html`;
        var file = fs.createWriteStream(ourFileName);
        response.pipe(file);
        break;
      }
      default:
        console.log(`${response.statusCode} -- ${botanical_name}  -- not logged`);
        const ourFileName = `${pngsPath}/other/${getKabobedName(
          botanical_name
        )}_${response.statusCode}.html`;
        var file = fs.createWriteStream(ourFileName);
        response.pipe(file);

        break;
    }
  });
};

const list = parseCsv(inputFileName);

const httpPicker = new HttpPicker(http, https);

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
          return writeImageFile(mediaURL, item.botanical_name, httpPicker, fs);
        }
      })
      .then(x => {
        console.log(`${item.EOL_ID}: ${item.botanical_name}: ${mediaURL}\n`);
      })
      .catch(err => console.log(`${item.EOL_ID}: ${err}`));
  } else {
    console.log(`${item.EOL_ID}: ${item.botanical_name}`);
  }
});
